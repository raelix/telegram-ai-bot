from typing import List, Dict
from langchain.schema import Document
from graph.agent import AgentWrapper


class AIManager:

    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key
        self.agents: Dict[str, AgentWrapper] = dict()

    def get_agent(self, user_id: str):
        if user_id not in self.agents:
            self.agents[user_id] = AgentWrapper(self.openai_api_key, user_id)
        return self.agents[user_id]

    def process_document(self, user_id: str, docs: List[Document], msg_id: int):
        agent = self.get_agent(user_id)
        agent.add_document(docs, msg_id)

    def ask(self, user_id: str, query: str):
        agent = self.get_agent(user_id)
        return agent.run(query)

    def get_features(self, user_id: str):
        agent = self.get_agent(user_id)
        return agent.get_features()

    def enable_feature(self, user_id: str, tool_name: str, values: Dict[str, str]):
        agent = self.get_agent(user_id)
        return agent.enable_feature(tool_name, values)

    def disable_feature(self, user_id: str, tool_name: str):
        agent = self.get_agent(user_id)
        return agent.disable_feature(tool_name)

    def get_features_status(self, user_id: str):
        agent = self.get_agent(user_id)
        return agent.get_features_status()

    def get_feature_parameters(self, user_id: str, tool_name: str):
        agent = self.get_agent(user_id)
        return agent.get_feature_parameters(tool_name)

    def get_available_feature_commands(self, user_id: str):
        agent = self.get_agent(user_id)
        return agent.get_available_feature_commands()

    def call_feature_command(self, user_id: str, tool_name: str, command: str):
        agent = self.get_agent(user_id)
        return agent.call_feature_command(tool_name, command)
