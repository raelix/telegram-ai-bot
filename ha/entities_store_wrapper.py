from typing import List
from langchain.embeddings import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from langchain.tools import Tool
from langchain.vectorstores.chroma import Chroma
from langchain.agents.agent_toolkits import create_retriever_tool
import logging
from langchain.retrievers.multi_query import MultiQueryRetriever
import utils
from ha.ha_handler import HAHandler


def _set_logger():
    logging.basicConfig()
    logging.getLogger("langchain.retrievers.multi_query").setLevel(logging.INFO)
    logging.getLogger("langchain.retrievers.multi_vector").setLevel(logging.INFO)


class EntitiesStoreWrapper:
    db_path: str = "./production_database"

    _NAME = "entities-extractor"
    _DESCRIPTION = """This tool allows to extract the home-assistant identifier of the entities.
    It is required before running any operation to get or execute an action on home-assistant."""

    def __init__(self, openai_api_key: str, user_id: str, ha_handler: HAHandler, **kwargs):
        _set_logger()
        self.openai_api_key = openai_api_key
        self.user_id = user_id
        self.embeddings = OpenAIEmbeddings(openai_api_key=self.openai_api_key, model=utils.EMBEDDINGS_MODEL)
        self.ha_handler = ha_handler
        self._init_db()

    def _init_db(self):
        self.db = Chroma(persist_directory=self.db_path,
                         embedding_function=self.embeddings,
                         collection_name="entities_{}".format(self.user_id))

    def add_document(self, documents: List[Document]):
        self.db.add_documents(documents)

    def process_home_assistant_entities(self):
        self.db.delete_collection()
        docs = self.ha_handler.get_summary()
        self._init_db()
        self.add_document(docs)

    def as_tool(self, llm, **kwargs) -> Tool:
        prompt = PromptTemplate(
            input_variables=["question"],
            template="""You are an AI language model assistant. Your task is 
            to generate only one different versions of the given user 
            question to retrieve relevant home-assistant entities.
            Generally light and switch are called light so try to ask for switches and lights. 
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
