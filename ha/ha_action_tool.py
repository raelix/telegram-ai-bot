from typing import Type
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from ha.ha_handler import HAHandler


class HaActionToolInput(BaseModel):
    entity_id: str = Field(description="The home-assistant entity identifier.")
    entity_type: str = Field(description="The home-assistant entity type.")
    action: str = Field(description="The home-assistant action to run.")


class HaActionTool(BaseTool):
    name:str = "home_assistant_action"
    description:str = """
        Required when you have to execute an action on a entity of home-assistant.
        The entity_id, entity_type and the action must match with the ones provided by the entities-extractor tool.
        """
    args_schema: Type[BaseModel] = HaActionToolInput

    def _run(self, entity_id: str, entity_type: str, action: str):
        ha_handler: HAHandler = self.metadata["ha_handler"]
        res = ha_handler.set_state(entity_type=entity_type, entity_id=entity_id, action=action)
        message = "The action {} has been executed on {}".format(action, entity_id)
        if res:
            return message
        else:
            return "Error, the action {} has not been executed on {}".format(action, entity_id)

    def _arun(self, entity_id: str, entity_type: str, action: str):
        raise NotImplementedError("home_assistant_action does not support async")
