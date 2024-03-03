from typing import List, Any, Dict
from langchain_openai import ChatOpenAI
from langchain.chat_models.base import BaseChatModel
from langchain.memory.chat_memory import BaseChatMemory
from langchain.prompts import MessagesPlaceholder, ChatPromptTemplate
from langchain.schema import Document, SystemMessage
from langchain.schema.runnable import RunnableSerializable
from langchain.tools import Tool
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain_core.utils.function_calling import convert_to_openai_function
from agent.function_agent_output_parser import CustomOpenAIFunctionsAgentOutputParser, Response
from settings.user_settings import UserSettings
from tools.tools_manager import ToolsManager
from langchain.memory import ConversationBufferWindowMemory
from langchain.agents import AgentExecutor
import utils
import chromadb

from vectorstore.vector_store_wrapper import VectorStoreWrapper


@DeprecationWarning
class AgentWrapper:
    _temperature: int = 0
    _max_win_memory: int = 3
    _agent_max_iterations: int = 30
    _agent_max_execution_time: int = 60  # seconds
    _openai_timeout: int = 40  # seconds
    _memory_key: str = "memory"

    def __init__(self, openai_api_key: str, user_id: str):
        self.openai_api_key = openai_api_key
        self.user_id = user_id
        self.user_settings = UserSettings(user_id)
        self.tools_manager = ToolsManager(self.openai_api_key,
                                          self.user_id,
                                          self.user_settings)
        self.db = VectorStoreWrapper(openai_api_key, user_id)
        # we don't want to re-initialize memory
        self.memory: BaseChatMemory = ConversationBufferWindowMemory(memory_key=self._memory_key,
                                                                     return_messages=True,
                                                                     k=self._max_win_memory,
                                                                     output_key="output")
        self.agent_executor = self._init_agent()

    def _init_agent(self):
        llm = ChatOpenAI(
            openai_api_key=self.openai_api_key,
            model=utils.AGENT_MODEL,
            temperature=self._temperature,
            request_timeout=self._openai_timeout)

        prompt = self._get_prompt()
        tools = self._get_tools(llm)
        agent = self._get_agent(prompt, llm, tools)

        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            memory=self.memory,
            return_intermediate_steps=True,
            max_iterations=self._agent_max_iterations,
            max_execution_time=self._agent_max_execution_time
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

    def _get_prompt(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages(
            [
                SystemMessage(content="You are very powerful assistant AI "
                                      "you can use the memory to access the history."),
                MessagesPlaceholder(variable_name=self._memory_key),
                ("user", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

    def _get_tools(self, llm: BaseChatModel) -> List[Tool]:
        tools = [self.db.as_tool(llm)] + self.tools_manager.get_user_tools(llm=llm)
        return tools

    @staticmethod
    def _get_agent(prompt: ChatPromptTemplate, llm: BaseChatModel, tools: List[Tool]) -> RunnableSerializable:
        return (
                {
                    "input": lambda x: x["input"],
                    "agent_scratchpad": lambda x: format_to_openai_function_messages(
                        x["intermediate_steps"]
                    ),
                    "intermediate_steps": lambda x: x["intermediate_steps"],
                    "memory": lambda x: x["memory"],
                }
                | prompt
                | llm.bind(functions=[convert_to_openai_function(t) for t in tools] +
                                     [convert_to_openai_function(Response)])
                | CustomOpenAIFunctionsAgentOutputParser()
        )

    def get_features(self):
        return self.tools_manager.get_tools_list()

    def get_feature_parameters(self, tool_name: str):
        return self.tools_manager.get_tool_required_parameters(tool_name)

    def enable_feature(self, tool_name: str, values: Dict[str, str]):
        self.tools_manager.set_tool_parameters(tool_name, values)
        # Recreate the agent with new enabled tools
        self.agent_executor = self._init_agent()

    def disable_feature(self, tool_name: str):
        self.tools_manager.disable_tool(tool_name)
        # Recreate the agent without disabled tool
        self.agent_executor = self._init_agent()

    def get_features_status(self):
        return self.tools_manager.get_tools_status()

    def get_available_feature_commands(self):
        return self.tools_manager.get_available_tools_functions()

    def call_feature_command(self, tool_name: str, command: str):
        self.tools_manager.call_tool_function(tool_name=tool_name, function_name=command)
        # Recreate the agent with the updated data
        self.agent_executor = self._init_agent()
