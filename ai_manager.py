from typing import List, Dict
from langchain.schema import Document
from agent_wrapper import AgentWrapper


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
