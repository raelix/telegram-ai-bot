from typing import Type
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from tools.movies.movies_handler import MoviesHandler


class NetflixPlayerToolInput(BaseModel):
    movie_id: str = Field(description="The movie id to play.")


class NetflixPlayerTool(BaseTool):
    name:str = "netflix_player"
    description:str = """
        Use this tool to play a movie if the user requested to watch it.
        Important: Never pass me the movie name but always the id of the movie (e.g. 81281344).
        If you don't know you can try searching on web.
        """
    args_schema: Type[BaseModel] = NetflixPlayerToolInput

    def _run(self, movie_id: str):
        movies_handler: MoviesHandler = self.metadata["movies_handler"]
        return movies_handler.watch(movie_id=movie_id)

    def _arun(self, entity_id: str, entity_type: str, action: str):
        raise NotImplementedError("netflix_player does not support async")
