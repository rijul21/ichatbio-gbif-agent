import pytest
from ichatbio.test_utils import InMemoryResponseChannel
from ichatbio.agent_response import ResponseContext, ArtifactResponse
from src.agent import GBIFAgent


@pytest.fixture
def run_agent():
    async def _run(entrypoint: str, user_message: str) -> dict:
        messages = []
        context = ResponseContext(InMemoryResponseChannel(messages))
        await GBIFAgent().run(context, user_message, entrypoint, None)

        artifacts = [m for m in messages if isinstance(m, ArtifactResponse)]
        artifact = artifacts[-1] if artifacts else None

        if not artifact:
            return {}

        return {"description": artifact.description}

    return _run