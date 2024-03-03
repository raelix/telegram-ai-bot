import abc
from pydantic.v1 import Field, BaseModel, Extra
from typing import List, Dict
from langchain.tools import Tool
from abc import abstractmethod


class ToolInstance(BaseModel, abc.ABC):
    openai_api_key: str = Field(description="The openai API Key")
    user_id: str = Field(description="The user identifier")

    class Config:
        extra = Extra.allow

    @classmethod
    @abstractmethod
    def init(cls, **kwargs):
        """ initialize sub class """

    @abstractmethod
    def get_tools(self, **kwargs) -> List[Tool]:
        """ return the tools exposed by the child """

    @classmethod
    @abstractmethod
    def get_available_functions(cls) -> Dict[str, str]:
        """ return the exposed functions [function name, function description]"""

    @classmethod
    def get_required_fields(cls, alias=False):
        return cls.schema(alias).get("properties")
