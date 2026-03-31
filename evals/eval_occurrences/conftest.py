import pytest
from ichatbio.test_utils import InMemoryResponseChannel
from ichatbio.agent_response import ResponseContext, DirectResponse, ProcessLogResponse
from src.agent import GBIFAgent

PARAM_LOG_TEXTS = {
    "Search API parameters results -",  # count entrypoint
    "Final Search API parameters",      # search entrypoint
    "Generated search parameters",      # find_occurrence_by_id entrypoint
}

def _extract_params(data: dict) -> dict:
    obj = data.get("search_params") or data
    source = vars(obj) if hasattr(obj, "__dict__") else obj
    return {k: v for k, v in source.items() if v is not None}


@pytest.fixture
def run_agent():
    async def _run(entrypoint: str, user_message: str) -> dict:
        messages = []
        context = ResponseContext(InMemoryResponseChannel(messages))
        await GBIFAgent().run(context, user_message, entrypoint, None)

        reply = next((m.text for m in messages if isinstance(m, DirectResponse)), "")
        params = next(
            (_extract_params(m.data or {}) for m in messages
             if isinstance(m, ProcessLogResponse) and m.text in PARAM_LOG_TEXTS),
            {}
        )

        return {"reply": reply, "params": params}

    return _run