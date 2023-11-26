from typing import List, Any
from langchain.chat_models import ChatOpenAI
from langchain.memory.chat_memory import BaseChatMemory
from langchain.prompts import MessagesPlaceholder
from langchain.schema import Document
from langchain.schema.callbacks.base import BaseCallbackHandler
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
        self.memory: BaseChatMemory = ConversationBufferWindowMemory(memory_key="memory",
                                                                     return_messages=True,
                                                                     k=self.max_win_memory,
                                                                     output_key="output")
        self.agent = self._init_agent(openai_api_key)

    def _init_agent(self, openai_api_key: str):
        self.llm = ChatOpenAI(openai_api_key=openai_api_key, model=utils.AGENT_MODEL, temperature=self.temperature)
        self.ch = CallbackHandler()
        callbacks = [self.ch]
        tools = [self.db.as_tool(self.llm, callbacks)] + get_ext_tools()
        agent = initialize_agent(
            tools,
            self.llm,
            agent=AgentType.OPENAI_FUNCTIONS,
            verbose=True,
            agent_kwargs=self._agent_kwargs,
            memory=self.memory,
            return_intermediate_steps=True,
            return_source_documents=True,
            # callback_manager=CallbackManager(callbacks)
        )
        # return AgentExecutor(agent=agent, tools=tools, verbose=True)
        return agent

    def run(self, query: str):
        result = self.agent({'input': query})
        # msg_id = _extract_id_from_intermediate_steps(result["intermediate_steps"])
        msg_id = self.ch.msg_id
        output = dict(
            response=result['output'],
            message_id=msg_id
        )
        # Reset
        self.ch.msg_id = None
        return output

    def add_document(self, docs: List[Document], msg_id: int, **kwargs: Any):
        self.db.add_document(docs, msg_id, **kwargs)


def _extract_id_from_intermediate_steps(intermediate_steps):
    for iterations in intermediate_steps:
        if iterations and isinstance(iterations, tuple):
            for iteration in iterations:
                if iteration and isinstance(iteration, list):
                    for item in iteration:
                        if item and isinstance(item, Document):
                            return item.metadata['message_id']


class CallbackHandler(BaseCallbackHandler):
    msg_id = None

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        if "name" in kwargs and kwargs["name"] == "document-extractor":
            docs: List[Document] = eval(output)
            if len(docs) > 0:
                self.msg_id = (docs[len(docs) - 1]).metadata["message_id"]
