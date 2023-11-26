from typing import List, Any
from langchain.chat_models import ChatOpenAI
from langchain.memory.chat_memory import BaseChatMemory
from langchain.prompts import MessagesPlaceholder
from langchain.schema import Document
from vector_store_wrapper import VectorStoreWrapper
from langchain.memory import ConversationBufferWindowMemory
from external_tools import get_ext_tools
from langchain.agents import AgentType, initialize_agent
import utils
import chromadb


class AgentWrapper:
    temperature: int = 0
    max_win_memory: int = 3
    _agent_kwargs = {
        "extra_prompt_messages": [MessagesPlaceholder(variable_name="memory")],
    }

    def __init__(self, openai_api_key: str, user_id: str):
        self.db = VectorStoreWrapper(openai_api_key, user_id)
        self.memory: BaseChatMemory = ConversationBufferWindowMemory(memory_key="memory", return_messages=True,
                                                                     k=self.max_win_memory)
        self.agent = self._init_agent(openai_api_key)

    def _init_agent(self, openai_api_key: str):
        self.llm = ChatOpenAI(openai_api_key=openai_api_key, model=utils.AGENT_MODEL, temperature=self.temperature)
        tools = [self.db.as_tool(self.llm)] + get_ext_tools()
        agent = initialize_agent(
            tools,
            self.llm,
            agent=AgentType.OPENAI_FUNCTIONS,
            verbose=True,
            agent_kwargs=self._agent_kwargs,
            memory=self.memory,
        )
        # return AgentExecutor(agent=agent, tools=tools, verbose=True)
        return agent

    def run(self, query: str):
        return self.agent({'input': query})['output']

    def add_document(self, docs: List[Document], **kwargs: Any):
        # summary = summarize(self.llm, docs)
        # for doc in docs:
        #     doc.metadata["summary"] = summary
        self.db.add_document(docs, **kwargs)
