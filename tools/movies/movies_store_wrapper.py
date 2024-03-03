from typing import List
from langchain_openai import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from langchain.tools import Tool
from langchain.vectorstores.chroma import Chroma
from langchain.agents.agent_toolkits import create_retriever_tool
import logging
from langchain.retrievers.multi_query import MultiQueryRetriever
from tools.movies.movies_handler import MoviesHandler
import utils


def _set_logger():
    logging.basicConfig()
    logging.getLogger("langchain.retrievers.multi_query").setLevel(logging.INFO)
    logging.getLogger("langchain.retrievers.multi_vector").setLevel(logging.INFO)


class MoviesStoreWrapper:
    db_path: str = "./movies_database"

    _NAME = "movies-retriever"
    _DESCRIPTION = """Use this tool to retrieve information about movies."""

    def __init__(self, openai_api_key: str, user_id: str, movies_handler: MoviesHandler, **kwargs):
        _set_logger()
        self.openai_api_key = openai_api_key
        self.user_id = user_id
        self.embeddings = OpenAIEmbeddings(openai_api_key=self.openai_api_key, model=utils.EMBEDDINGS_MODEL)
        self.movies_handler = movies_handler
        self._init_db()

    def _init_db(self):
        self.db = Chroma(persist_directory=self.db_path,
                         embedding_function=self.embeddings,
                         collection_name="movies_{}".format(self.user_id))

    def add_document(self, documents: List[Document]):
        self.db.add_documents(documents)

    def process_movies(self):
        self.db.delete_collection()
        docs = self.movies_handler.get_docs()
        self._init_db()
        self.add_document(docs)

    def as_tool(self, llm, **kwargs) -> Tool:
        prompt = PromptTemplate(
            input_variables=["question"],
            template="""You are an AI movies retriever. Your task is 
            to generate only one different versions of the given user 
            question to retrieve relevant movies based on the user request.
            By generating multiple perspectives on the user question, 
            your goal is to help the user overcome some of the limitations 
            of distance-based similarity search. Provide these alternative 
            questions separated by newlines. Original question: {question}""",
        )
        retriever = MultiQueryRetriever.from_llm(
            retriever=self.db.as_retriever(k=10),
            prompt=prompt,
            llm=llm,
            include_original=True
        )
        tool = create_retriever_tool(
            retriever,
            name=self._NAME,
            description=self._DESCRIPTION,
        )
        return tool
