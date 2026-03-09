"""
Pytest configuration file.
"""
import pytest
from ichatbio.agent_response import ResponseChannel, ResponseContext, ResponseMessage
from src.agent import GBIFAgent

class InMemoryResponseChannel(ResponseChannel):
    def __init__(self, message_buffer: list):
        self.message_buffer = message_buffer
        self.task_id = "617727d1-4ce8-4902-884c-db786854b51c"

    async def submit(self, message: ResponseMessage):
        self.message_buffer.append(message)

@pytest.fixture(scope="function")
def agent():
    return GBIFAgent()

@pytest.fixture(scope="function")
def messages() -> list[ResponseMessage]:
    return []

@pytest.fixture(scope="function")
def context(messages) -> ResponseContext:
    return ResponseContext(InMemoryResponseChannel(messages))