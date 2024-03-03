from typing import List, Dict, Type
from langchain_community.tools import Tool
from langchain_core.tools import BaseTool
from pydantic.v1 import BaseModel, Field
from langchain_community.document_loaders import AsyncHtmlLoader
import re
from tools.tool_instance import ToolInstance
from langchain_community.tools import DuckDuckGoSearchRun

from vectorstore.utils import generic


class NetflixIdDiscoveryCustomTool(ToolInstance):

    @classmethod
    def init(cls, **kwargs):
        return cls(**kwargs)

    def get_tools(self, **kwargs) -> List[BaseTool]:
        return [
            NetflixIdDiscoveryTool(metadata=dict(openai_api_key=self.openai_api_key))
        ]

    @classmethod
    def get_available_functions(cls) -> Dict[str, str]:
        return dict()


class NetflixIdScraperToolInput(BaseModel):
    movie_name: str = Field(description="The movie name to search the netflix id.")


class NetflixIdDiscoveryTool(BaseTool):
    name = "netflix_id_discovery"
    description = """
        Use this tool to search the netflix id of a movie only when movies-retriever doesn't have a good answer.
        Always prefer to search first in the movies-retriever.
        The output will be the netflix id if found.
        """
    args_schema: Type[BaseModel] = NetflixIdScraperToolInput

    def _run(self, movie_name: str):
        openai_api_key: str = self.metadata["openai_api_key"]
        urls = [f"https://www.google.com/search?q={movie_name}+on+netflix"]
        loader = AsyncHtmlLoader(urls)
        docs = loader.load()
        urls = self.extract_urls(docs[0].page_content)
        urls_text = ','.join(urls)
        return generic(openai_api_key, "You are a very powerful AI assistant"
                                       "you are able to extract the netflix id of a movie from a list of urls."
                                       "The id is generally after title/ path in the url."
                                       "Return only the id you found without any other text or just say that it's not "
                                       "available. Do not invent.",
                       urls_text)[0]

    def _arun(self, movie_name: str):
        raise NotImplementedError("netflix_id_discovery does not support async")

    def extract_urls(self, text):
        url_pattern = r'https?://\S+'
        urls = re.findall(url_pattern, text)
        return urls
