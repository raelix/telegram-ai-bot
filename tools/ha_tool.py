from pydantic import Field
from typing import List, Dict
from langchain.chat_models.base import BaseChatModel
from langchain.tools import Tool
from ha.entities_store_wrapper import EntitiesStoreWrapper
from ha.ha_handler import HAHandler
from ha.ha_action_tool import HaActionTool
from ha.ha_status_tool import HAStatusTool
from tools.tool_instance import ToolInstance


class HATool(ToolInstance):
    url: str = Field(description="Home Assistant URL")
    bearer_token: str = Field(description="The bearer token to authenticate on Home Assistant")
    # private vars
    _ha_db: EntitiesStoreWrapper
    _ha_handler: HAHandler

    @classmethod
    def init(cls, **kwargs):
        ha_handler = HAHandler(**kwargs)
        ha_db = EntitiesStoreWrapper(ha_handler=ha_handler, **kwargs)
        return cls(
            _ha_db=ha_db,
            _ha_handler=ha_handler,
            **kwargs)

    def get_tools(self, llm: BaseChatModel, **kwargs) -> List[Tool]:
        return [
            self._ha_db.as_tool(llm),
            HAStatusTool(metadata=dict(ha_handler=self._ha_handler)),
            HaActionTool(metadata=dict(ha_handler=self._ha_handler))
        ]

    @classmethod
    def get_available_functions(cls) -> Dict[str, str]:
        return dict(
            reprocess_data="Reload Home Assistant entities and definitions"
        )

    def reprocess_data(self):
        self._ha_db.process_home_assistant_entities()
