# os utility for Python OS related calls
import os

#load environment variables from the .env file
from dotenv import load_dotenv
load_dotenv()

#pydantic conversion of string using Secret 
from pydantic import SecretStr

#lang chain objects
from langchain_openai import ChatOpenAI #Open AI chat model

# llm object - Nous Research API for Large Language Model
# Nous Research is compatible with the OpenAI API, so we can use the ChatOpenAI class
llm = ChatOpenAI(
    model=os.environ["NOUS_MODEL"],  # list available models: GET /v1/models on the base_url
    api_key=SecretStr(os.environ["NOUS_API_KEY"]),  # key read from the environment, set in .env
    base_url="https://inference-api.nousresearch.com/v1",
)