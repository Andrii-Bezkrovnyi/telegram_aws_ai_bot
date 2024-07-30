import os
import textwrap
from loguru import logger

from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.document_loaders import WebBaseLoader
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings

# Load environment variables from .env file
load_dotenv()

# Set your OpenAI API key here
api_key = os.getenv("OPENAI_API_KEY")

logger.add("bot_info.log", level="INFO", format="{time} - {level} - {message}")

URL = "https://www.amazon.co.uk/gp/help/customer/display.html?nodeId=GKM69DUUYKQWKWX7"

embeddings = OpenAIEmbeddings()


def create_db_from_url():
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


def get_response_from_query(db, query):
    retriever = db.as_retriever(k=4)
    docs = retriever.invoke(query)

    llm = ChatOpenAI(api_key=api_key, model_name="gpt-3.5-turbo", temperature=0.1)

    # Updated prompt template to handle unrelated queries
    prompt = PromptTemplate(
        input_variables=["question", "docs"],
        template="""
        You are a  assistant that can answer questions about Amazon's return policy based on the information in the documents.

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


db = create_db_from_url()


def main():
    logger.info("Hello! I can help you with information about Amazon's return policy. How can I assist you today?")
    logger.info("Type 'exit' or 'quit' to end the chat.\n")

    while True:
        user_query = input("Enter your question: ")
        if user_query.lower() in ['exit', 'quit']:
            print("Goodbye! Have a nice day")
            break
        response, docs = get_response_from_query(db, user_query)
        bot_answer = textwrap.fill(response, width=85)
        print(f"\nBot answer:\n{bot_answer}\n")


if __name__ == '__main__':
    main()
