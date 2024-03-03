from typing import List, Any, Dict
from langchain_openai import ChatOpenAI
from langchain.prompts import MessagesPlaceholder, ChatPromptTemplate
from langchain.schema import Document, SystemMessage
from langchain.schema.runnable import RunnableSerializable
from langchain_core.utils.function_calling import convert_to_openai_function
from langgraph.prebuilt import ToolExecutor
from graph.graph import Graph
from graph.nodes import Nodes
from graph.response import Response
from settings.user_settings import UserSettings
from tools.tools_manager import ToolsManager
import utils
from vectorstore.vector_store_wrapper import VectorStoreWrapper


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
        self.llm = ChatOpenAI(
            openai_api_key=self.openai_api_key,
            model=utils.AGENT_MODEL,
            temperature=self._temperature,
            request_timeout=self._openai_timeout)
        self.db = VectorStoreWrapper(self.openai_api_key, self.user_id)
        user_settings = UserSettings(self.user_id)
        self.tools_manager = ToolsManager(self.openai_api_key, self.user_id, user_settings)
        self.tools, self.tool_executor = self.init_tools(self.tools_manager, self.llm, self.db)
        self.model = self.init_model(self.tools)
        self.nodes = Nodes(self.model, self.tool_executor)
        self.graph = Graph(self.nodes)

    def init_model(self, tools) -> RunnableSerializable:
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are very powerful assistant AI when possible return the final answer"
                    " using the tool Response including the message_id."
                    " Reply always with the user language."
                ),
                MessagesPlaceholder(variable_name="memory", optional=True),
                MessagesPlaceholder(variable_name="messages", optional=False)
            ]
        )
        f_tools = [convert_to_openai_function(t) for t in tools]
        f_tools.append(convert_to_openai_function(Response))
        return (
                {
                    "memory": lambda x: x["memory"],
                    "messages": lambda x: x["messages"],
                }
                | prompt
                | self.llm.bind_tools(tools=f_tools)
        )

    def init_tools(self, tool_manager, llm, db):
        tools = [db.as_tool(llm)] + tool_manager.get_user_tools(llm=llm)
        return tools, ToolExecutor(tools)

    def re_init_agent(self):
        user_settings = UserSettings(self.user_id)
        self.tools_manager = ToolsManager(self.openai_api_key, self.user_id, user_settings)
        self.tools, self.tool_executor = self.init_tools(self.tools_manager, self.llm, self.db)
        user_settings = UserSettings(self.user_id)
        self.tools_manager = ToolsManager(self.openai_api_key, self.user_id, user_settings)
        self.model = self.init_model(self.tools)
        self.nodes = Nodes(self.model, self.tool_executor)
        self.graph = Graph(self.nodes)

    def run(self, question: str) -> dict[str, Any | None]:
        return self.graph.run(question)

    def add_document(self, docs: List[Document], msg_id: int, **kwargs: Any):
        self.db.add_document(docs, msg_id, **kwargs)

    def get_features(self):
        return self.tools_manager.get_tools_list()

    def get_feature_parameters(self, tool_name: str):
        return self.tools_manager.get_tool_required_parameters(tool_name)

    def enable_feature(self, tool_name: str, values: Dict[str, str]):
        self.tools_manager.set_tool_parameters(tool_name, values)
        # Recreate the agent with new enabled tools
        self.re_init_agent()

    def disable_feature(self, tool_name: str):
        self.tools_manager.disable_tool(tool_name)
        # Recreate the agent without disabled tool
        self.re_init_agent()

    def get_features_status(self):
        return self.tools_manager.get_tools_status()

    def get_available_feature_commands(self):
        return self.tools_manager.get_available_tools_functions()

    def call_feature_command(self, tool_name: str, command: str):
        self.tools_manager.call_tool_function(tool_name=tool_name, function_name=command)
        # Recreate the agent with the updated data
        self.re_init_agent()
