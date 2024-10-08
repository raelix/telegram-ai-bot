from typing import List, Any
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
from langchain.tools import Tool
from langchain_community.vectorstores import Chroma
from langchain.agents.agent_toolkits import create_retriever_tool
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.storage._lc_store import create_kv_docstore
import logging
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.retrievers.multi_vector import MultiVectorRetriever
from vectorstore.chroma_docstore import ChromaStore
from vectorstore.utils import questions, summaries
import utils
import uuid


def _set_logger():
    logging.basicConfig()
    logging.getLogger("langchain.retrievers.multi_query").setLevel(logging.INFO)
    logging.getLogger("langchain.retrievers.multi_vector").setLevel(logging.INFO)


class VectorStoreWrapper:
    db_path: str = "./production_database"
    store_path: str = "./production_store"
    id_key: str = "doc_id"

    _NAME = "document-extractor"
    _DESCRIPTION = """This tool allows to extract personal stored information, all the user documents are available 
    here. Provide me an exhaustive sentence. Do your best to find an answer."""

    def __init__(self, openai_api_key: str, user_id: str):
        _set_logger()
        self.openai_api_key = openai_api_key
        self.embeddings = OpenAIEmbeddings(openai_api_key=self.openai_api_key, model=utils.EMBEDDINGS_MODEL)
        vector_store = Chroma(persist_directory=self.db_path,
                              embedding_function=self.embeddings,
                              collection_name=user_id)
        cs = ChromaStore(self.db_path, user_id)
        store = create_kv_docstore(cs)
        # MultiVector - Summaries & Possible Questions
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=2000)
        self.db = MultiVectorRetriever(
            vectorstore=vector_store,
            docstore=store,
            id_key=self.id_key,
            k=4,
        )
        # Parent Doc retriever
        # parent_splitter = RecursiveCharacterTextSplitter(chunk_size=2000)
        # child_splitter = RecursiveCharacterTextSplitter(chunk_size=400)
        # self.db = ParentDocumentRetriever(
        #     vectorstore=vector_store,
        #     docstore=store,
        #     parent_splitter=parent_splitter,
        #     child_splitter=child_splitter,
        # )

    def add_document(self, documents: List[Document], msg_id: int, **kwargs: Any):
        # Parent Doc retriever
        # self.db.add_documents(documents, ids=None, **kwargs)
        # documents = self.splitter.split_documents(documents)
        doc_ids = [str(uuid.uuid4()) for _ in documents]
        ret_docs = []
        print('creating questions')
        question_docs = questions(self.openai_api_key, documents)
        print('creating summary')
        summaries_docs = summaries(self.openai_api_key, documents)
        for i, question_list in enumerate(question_docs):
            ret_docs.extend(
                [Document(page_content=s, metadata={self.id_key: doc_ids[i]}) for s in question_list]
            )
        for i, summary in enumerate(summaries_docs):
            ret_docs.append(
                Document(page_content=summary, metadata={self.id_key: doc_ids[i]})
            )
        for doc in documents:
            doc.metadata["message_id"] = msg_id
            doc.page_content += f"\n\nmessage_id: {msg_id}"
        print('questions and summary created')
        self.db.vectorstore.add_documents(ret_docs)
        self.db.docstore.mset(list(zip(doc_ids, documents)))

    def as_tool(self, llm) -> Tool:
        retriever = MultiQueryRetriever.from_llm(
            retriever=self.db,
            llm=llm,
            include_original=False
        )
        tool = create_retriever_tool(
            retriever,
            name=self._NAME,
            description=self._DESCRIPTION,
        )
        return tool
