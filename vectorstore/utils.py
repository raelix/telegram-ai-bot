from typing import List

from langchain_openai import ChatOpenAI
from langchain.output_parsers.openai_functions import JsonKeyOutputFunctionsParser
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser, Document
import utils


def generic(openai_api_key: str, system_text: str, input_text: str):
    chain = (
            {"input": lambda x: x}
            | ChatPromptTemplate.from_template(f"{system_text}\n\n" + "{input}\n")
            | ChatOpenAI(openai_api_key=openai_api_key, max_retries=0, temperature=0, model=utils.AGENT_MODEL)
            | StrOutputParser()
    )

    return chain.batch([input_text], {"max_concurrency": 5})


def summaries(openai_api_key: str, docs: List[Document]):
    chain = (
            {"doc": lambda x: x.page_content}
            | ChatPromptTemplate.from_template("Summarize the following document:\n\n{doc}")
            | ChatOpenAI(openai_api_key=openai_api_key, max_retries=0, temperature=0, model=utils.AGENT_MODEL)
            | StrOutputParser()
    )

    return chain.batch(docs, {"max_concurrency": 5})


def questions(openai_api_key: str, docs: List[Document]):
    functions = [
        {
            "name": "hypothetical_questions",
            "description": "Generate hypothetical questions",
            "parameters": {
                "type": "object",
                "properties": {
                    "questions": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["questions"],
            },
        }
    ]
    chain = (
            {"doc": lambda x: x.page_content}
            | ChatPromptTemplate.from_template(
        "Generate a list of 3 hypothetical questions that the below document could be used to answer:\n\n{doc}"
    )
            | ChatOpenAI(openai_api_key=openai_api_key, temperature=0, max_retries=0, model=utils.AGENT_MODEL).bind(
        functions=functions,
        function_call={"name": "hypothetical_questions"}
    )
            | JsonKeyOutputFunctionsParser(key_name="questions")
    )
    return chain.batch(docs, {"max_concurrency": 5})
