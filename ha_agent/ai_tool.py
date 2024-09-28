from typing import Type
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from ha_agent.query import HAAgentQuery


class HaAgentToolInput(BaseModel):
    sentence: str = Field(description="The sentence to send to home-assistant AI agent.")


class HAAgentAITool(BaseTool):
    name:str = "home_assistant_agent"
    description:str = """
        Allows to interact with home-assistant by getting/setting devices statuses.
        Always use this tool as domotic agent tool. It will return a JSON with the response inside, it allows continuos conversation.
        """
    args_schema: Type[BaseModel] = HaAgentToolInput

    def _run(self, sentence: str):
        ha_agent_query: HAAgentQuery = self.metadata["ha_agent_query"]
        status = ha_agent_query.query_sentence(sentence)
        if not status: #or not attributes:
            return ("Error while connecting to the home-assistant instance, "
                    "maybe the configuration is wrong")
        return f"The response status is {status}"#. Properties associated to this entity are {attributes}"

    def _arun(self, entity_id: str):
        raise NotImplementedError("home_assistant_status does not support async")
