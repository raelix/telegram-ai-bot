from typing import Type
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from tools.movies.movies_handler import MoviesHandler


class NetflixPlayerToolInput(BaseModel):
    movie_id: str = Field(description="The movie id to play.")


class NetflixPlayerTool(BaseTool):
    name = "netflix_player"
    description = """
        Use this tool to play a movie if the user requested to watch it.
        """
    args_schema: Type[BaseModel] = NetflixPlayerToolInput

    def _run(self, movie_id: str):
        movies_handler: MoviesHandler = self.metadata["movies_handler"]
        return movies_handler.watch(movie_id=movie_id)

    def _arun(self, entity_id: str, entity_type: str, action: str):
        raise NotImplementedError("netflix_player does not support async")
