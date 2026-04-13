import dotenv
dotenv.load_dotenv()
import pytest
from ichatbio.test_utils import InMemoryResponseChannel
from ichatbio.agent_response import ResponseContext, DirectResponse, ProcessLogResponse, ArtifactResponse
from src.agent import GBIFAgent

PARAM_LOG_TEXTS = {
    "Search API parameters results -",
    "Final Search API parameters",
    "Generated search parameters",
    "Final Search Parameters",
}

@pytest.fixture
def run_agent():
    async def _run(entrypoint: str, user_message: str) -> dict:
        messages = []
        context = ResponseContext(InMemoryResponseChannel(messages))
        await GBIFAgent().run(context, user_message, entrypoint, None)
        
        #extracting final reply
        reply = next((m.text for m in messages if isinstance(m, DirectResponse)), "")
        
        # taking out params from process logs
        params = {}
        for m in messages:
            if isinstance(m, ProcessLogResponse) and m.text in PARAM_LOG_TEXTS:
                obj = (m.data or {}).get("search_params") or m.data or {}
                src = vars(obj) if hasattr(obj, "__dict__") else obj
                params = {k: v for k, v in src.items() if v is not None}
                break
        
        #get the last final artifact 
        artifact = next((m for m in reversed(messages) if isinstance(m, ArtifactResponse)), None)
        
        return {
            "reply": reply,
            "params": params,
            "description": artifact.description if artifact else "",
            "portal_url": (artifact.metadata or {}).get("portal_url", "") if artifact else "",
        }
    return _run
