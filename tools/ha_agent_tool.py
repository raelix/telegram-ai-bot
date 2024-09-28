from pydantic.v1 import Field
from typing import List, Dict
from langchain.chat_models.base import BaseChatModel
from langchain.tools import Tool
from ha_agent.query import HAAgentQuery
from ha_agent.ai_tool import HAAgentAITool
from tools.tool_instance import ToolInstance


class HAAgentTool(ToolInstance):
    url: str = Field(description="Home Assistant URL")
    bearer_token: str = Field(description="The bearer token to authenticate on Home Assistant")
    _ha_agent_query: HAAgentQuery


    @classmethod
    def init(cls, **kwargs):
        ha_agent_query = HAAgentQuery(**kwargs)
        return cls(
            _ha_agent_query=ha_agent_query,
            **kwargs)

    def get_tools(self, llm: BaseChatModel, **kwargs) -> List[Tool]:
        return [
            HAAgentAITool(metadata=dict(ha_agent_query=self._ha_agent_query))
        ]

    @classmethod
    def get_available_functions(cls) -> Dict[str, str]:
        return dict()

