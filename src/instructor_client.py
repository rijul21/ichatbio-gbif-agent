import instructor
from openai import AsyncOpenAI

async def get_client():
    return instructor.from_openai(AsyncOpenAI(), model="gpt-4.1")
