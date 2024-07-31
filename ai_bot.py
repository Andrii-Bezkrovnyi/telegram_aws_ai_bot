import os
from typing import Optional, Tuple

from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.document_loaders import WebBaseLoader
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from loguru import logger

# Load environment variables from .env file
load_dotenv()

# Set your OpenAI API key here
api_key = os.getenv("OPENAI_API_KEY")

logger.add("bot_info.log", level="INFO", format="{time} - {level} - {message}")

URL = "https://www.amazon.co.uk/gp/help/customer/display.html?nodeId=GKM69DUUYKQWKWX7"

embeddings = OpenAIEmbeddings()


def create_db_from_url() -> Optional[Chroma]:
    """
    Loads and processes data from a given URL, splits the text into chunks, and stores
    it in a vector database using Chroma.

    Returns:
        Optional[Chroma]: A Chroma vectorstore object if successful, None if an error occurs.
    """
    try:
        loader = WebBaseLoader(web_paths=[URL],
                               bs_get_text_kwargs={
                                   "separator": " ",
                                   "strip": True,
                               })
        data = loader.load()
        if not data:
            raise ValueError("No data loaded from the URL.")

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        all_splits = text_splitter.split_documents(data)
        if not all_splits:
            raise ValueError("No text splits created from the data.")

        vectorstore = Chroma.from_documents(documents=all_splits, embedding=embeddings)

        return vectorstore

    except ValueError as err:
        logger.error(f"Value error: {err}")
    except Exception as err:
        logger.error(f"An error occurred: {err}")
    return None


def get_response_from_query(db: Chroma, query: str) -> Tuple[str, Optional[list]]:
    """
    Retrieves documents from the vector database based on a query and uses an LLM to generate a response.

    Args:
        db (Chroma): The Chroma vectorstore object for retrieving relevant documents.
        query (str): The user's query.

    Returns:
        Tuple[str, Optional[list]]: The generated response and the retrieved documents. If an error occurs,
        an error message is returned along with None.
    """
    try:
        retriever = db.as_retriever(k=4)
        docs = retriever.invoke(query)

        if not docs:
            raise ValueError("No documents retrieved for the query.")

        llm = ChatOpenAI(api_key=api_key, model_name="gpt-3.5-turbo", temperature=0.1)

        # Updated prompt template to handle unrelated queries
        prompt = PromptTemplate(
            input_variables=["question", "docs"],
            template="""
            You are an assistant that can answer questions about Amazon's return policy based on the information in the documents.

            Answer the following question: {question}
            By searching the following information: {docs}

            Only use the factual information from the docs to answer the question. If the question is not related to returning items, kindly respond with:
            "I don't know the answer to this question. Please, contact Amazon customer support for further assistance."

            Your answers should be detailed and relevant to the return policy.
            """,
        )

        formatted_prompt = prompt.format(question=query, docs=docs)
        response = llm.invoke(formatted_prompt)
        response_text = response.content.replace("\n", "")
        return response_text, docs

    except ValueError as err:
        print(f"Value Error: {err}")
        return f"Error: {err}", None

    except KeyError as key_err:
        print(f"Key Error: {key_err}")
        return f"Error: {key_err}", None

    except Exception as exc:
        print(f"An unexpected error occurred: {exc}")
        return f"An unexpected error occurred: {exc}", None
