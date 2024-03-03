from typing import List, Dict
from langchain.tools import Tool
from pydantic.v1 import Field
from langchain_community.utilities import GoogleSearchAPIWrapper
from tools.tool_instance import ToolInstance


class GoogleSearchTool(ToolInstance):
    google_api_key: str = Field(description="Google API Key")
    google_cse_id: str = Field(description="Google Search ID")

    @classmethod
    def init(cls, **kwargs):
        return cls(**kwargs)

    def get_tools(self, **kwargs) -> List[Tool]:
        gsa = GoogleSearchAPIWrapper(google_api_key=self.google_api_key, google_cse_id=self.google_cse_id)
        return [
            Tool(
                name="GoogleSearch",
                description="Search Google for recent results.",
                func=gsa.run,
            )
        ]

    @classmethod
    def get_available_functions(cls) -> Dict[str, str]:
        return dict()
