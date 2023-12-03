from typing import List, Dict
from langchain.tools import Tool
from tools.tool_instance import ToolInstance
from langchain.tools import DuckDuckGoSearchRun


class DuckDuckGoTool(ToolInstance):

    @classmethod
    def init(cls, **kwargs):
        return cls(**kwargs)

    def get_tools(self, **kwargs) -> List[Tool]:
        return [
            DuckDuckGoSearchRun()
        ]

    @classmethod
    def get_available_functions(cls) -> Dict[str, str]:
        return dict()


