from typing import Type
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from ha.ha_handler import HAHandler


class HaStatusToolInput(BaseModel):
    entity_id: str = Field(description="The home-assistant entity identifier.")


class HAStatusTool(BaseTool):
    name:str = "home_assistant_status"
    description:str = """
        Required when you have to get the status of an entity from home-assistant.
        The entity_id must match with the one provided by the entities-extractor tool.
        """
    args_schema: Type[BaseModel] = HaStatusToolInput

    def _run(self, entity_id: str):
        ha_handler: HAHandler = self.metadata["ha_handler"]
        status = ha_handler.get_entity_status(entity_id)
        if not status: #or not attributes:
            return ("Error while connecting to the home-assistant instance, "
                    "maybe the configuration is wrong")
        return f"The entity status is {status}"#. Properties associated to this entity are {attributes}"

    def _arun(self, entity_id: str):
        raise NotImplementedError("home_assistant_status does not support async")
