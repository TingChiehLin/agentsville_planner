from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(
    base_url="https://openai.vocareum.com/v1", api_key=os.getenv("OPENAI_API_KEY")
)
