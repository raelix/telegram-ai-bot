from pydantic.v1 import Field
from typing import List, Dict
from langchain.chat_models.base import BaseChatModel
from langchain.tools import Tool
from tools.movies.movies_handler import MoviesHandler
from tools.movies.movies_store_wrapper import MoviesStoreWrapper
from tools.movies.netflix_player import NetflixPlayerTool
from tools.tool_instance import ToolInstance


class MoviesTool(ToolInstance):
    movies_filename: str = Field(description="The local aggregated list of movies filename")
    webhook_url: str = Field(description="The Home Assistant webhook url to play movies by id")
    # private vars
    _movies_db: MoviesStoreWrapper
    _movies_handler: MoviesHandler

    @classmethod
    def init(cls, **kwargs):
        movies_handler = MoviesHandler(**kwargs)
        movies_db = MoviesStoreWrapper(movies_handler=movies_handler, **kwargs)
        return cls(
            _movies_db=movies_db,
            _movies_handler=movies_handler,
            **kwargs)

    def get_tools(self, llm: BaseChatModel, **kwargs) -> List[Tool]:
        return [
            self._movies_db.as_tool(llm),
            NetflixPlayerTool(metadata=dict(movies_handler=self._movies_handler)),
        ]

    @classmethod
    def get_available_functions(cls) -> Dict[str, str]:
        return dict(
            reprocess_data="Reload movies list",
        )

    def reprocess_data(self):
        self._movies_db.process_movies()
