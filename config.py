import os

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

ERROR_MESSAGE = 'We are facing a technical issue at this moment.'

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
BACKEND_URL = os.getenv('BACKEND_URL')
GPT_MODEL = os.getenv('GPT_MODEL')
