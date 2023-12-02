from typing import List, Any
from langchain.chat_models import ChatOpenAI
from langchain.memory.chat_memory import BaseChatMemory
from langchain.prompts import MessagesPlaceholder, ChatPromptTemplate
from langchain.schema import Document, SystemMessage
from langchain.tools.render import format_tool_to_openai_function
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.utils.openai_functions import convert_pydantic_to_openai_function
from function_agent_output_parser import CustomOpenAIFunctionsAgentOutputParser, Response
from vector_store_wrapper import VectorStoreWrapper
from langchain.memory import ConversationBufferWindowMemory
from external_tools import get_ext_tools
from langchain.agents import AgentExecutor
import utils
import chromadb


class AgentWrapper:
    _temperature: int = 0
    _max_win_memory: int = 3
    _agent_max_iterations: int = 4
    _agent_max_execution_time: int = 40  # seconds
    _openai_timeout: int = 40  # seconds
    _memory_key: str = "memory"

    def __init__(self, openai_api_key: str, user_id: str):
        self.db = VectorStoreWrapper(openai_api_key, user_id)
        self.memory: BaseChatMemory = ConversationBufferWindowMemory(memory_key=self._memory_key,
                                                                     return_messages=True,
                                                                     k=self._max_win_memory,
                                                                     output_key="output"
                                                                     )
        self.agent_executor = self._init_agent(openai_api_key)

    def _init_agent(self, openai_api_key: str):
        self.llm = ChatOpenAI(
            openai_api_key=openai_api_key,
            model=utils.AGENT_MODEL,
            temperature=self._temperature,
            request_timeout=self._openai_timeout)

        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content="You are very powerful assistant AI "
                                      "you can use the memory to access the history."),
                MessagesPlaceholder(variable_name=self._memory_key),
                ("user", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        tools = [self.db.as_tool(self.llm)] + get_ext_tools()

        agent = (
                {
                    "input": lambda x: x["input"],
                    "agent_scratchpad": lambda x: format_to_openai_function_messages(
                        x["intermediate_steps"]
                    ),
                    "intermediate_steps": lambda x: x["intermediate_steps"],
                    "memory": lambda x: x["memory"],
                }
                | prompt
                | self.llm.bind(functions=[format_tool_to_openai_function(t) for t in tools] +
                                          [convert_pydantic_to_openai_function(Response)])
                | CustomOpenAIFunctionsAgentOutputParser()
        )

        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            memory=self.memory,
            return_intermediate_steps=True,
            max_iterations=self._agent_max_iterations,
            max_execution_time=self._agent_max_execution_time,
            early_stopping_method="generate"
        )

    def run(self, query: str):
        result = self.agent_executor({'input': query})
        msg_id = None
        if "message_id" in result:
            msg_id = result["message_id"]
        output = dict(
            response=result['output'],
            message_id=msg_id
        )
        return output

    def add_document(self, docs: List[Document], msg_id: int, **kwargs: Any):
        self.db.add_document(docs, msg_id, **kwargs)
