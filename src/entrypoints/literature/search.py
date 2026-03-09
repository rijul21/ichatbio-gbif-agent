import uuid
import json

from ichatbio.agent_response import ResponseContext
from ichatbio.types import AgentEntrypoint

from src.gbif.api import GbifApi
from src.gbif.fetch import execute_request
from src.gbif.parser import parse
from src.models.literature import GBIFLiteratureSearchParams
from src.models.validators import LiteratureSearchParamsValidator
from src.log import with_logging, logger
from src.utils import (
    _generate_artifact_description,
    _preprocess_user_request,
    serialize_organisms,
    serialize_for_log,
)
from src.gadm.gadm import serialize_locations, map_locations_to_gadm


description = """
**Use Case:** Use this entrypoint to search for scientific literature (papers, theses, reports, etc.) that cites or uses GBIF-mediated biodiversity data.

**Triggers On:** User requests that ask to "find papers", "search for publications", "show literature", "find studies", "find research about", or "find articles" related to biodiversity topics.

**Key Inputs:** Accepts free-text search (q), publication type (literatureType), relevance to GBIF (relevance), year or year range, topics, peer-review status, open access status, country of researcher, country of coverage, and GBIF dataset keys.

**Limitations:** Only searches literature indexed by GBIF's literature tracking programme. Does not search all scientific literature.
"""

entrypoint = AgentEntrypoint(
    id="find_literature",
    description=description,
    parameters=None,
)


@with_logging("find_literature")
async def run(context: ResponseContext, request: str):
    """
    Executes the literature search entrypoint. Searches for publications that cite
    or use GBIF-mediated data and creates an artifact with the results.
    """
    async with context.begin_process("Searching GBIF Literature") as process:
        AGENT_LOG_ID = f"FIND_LITERATURE_{str(uuid.uuid4())[:6]}"
        logger.info(f"Agent log ID: {AGENT_LOG_ID}")
        await process.log(f"Request received: {request}\n\nParsing request...")

        expansion_response = await _preprocess_user_request(request)
        enrich_locations = []
        if expansion_response.locations:
            enrich_locations = await map_locations_to_gadm(expansion_response.locations)

        # Literature does not need Bionomia or GrSciColl entity resolution
        # but we pass organisms and locations to the parser for richer q field matching

        expanded_request = (
            f"User request: {request} "
            f"Identified organisms in the request: {json.dumps(serialize_organisms(expansion_response.organisms))} "
            f"Identified locations in the request: {json.dumps(serialize_locations(enrich_locations))}"
        )

        await process.log(
            "Expanded request",
            data={
                "original_request": request,
                "identified_organisms": serialize_organisms(expansion_response.organisms),
                "identified_locations": serialize_locations(enrich_locations),
            },
        )

        response = await parse(
            expanded_request,
            entrypoint.id,
            LiteratureSearchParamsValidator,
            expansion_response,
        )
        await process.log("Parameter parsing plan", data={"plan": response.plan})
        logger.info(f"Parameter parsing response: {response}")

        if response.clarification_needed:
            await process.log(
                f"Clarification needed: {response.clarification_reason}",
                data={"unresolved_params": response.unresolved_params},
            )
            await context.reply(response.clarification_reason)
            return

        search_params = response.params
        api = GbifApi()

        await process.log(
            "Final search parameters",
            data=serialize_for_log(search_params),
        )

        try:
            api_url = api.build_literature_search_url(search_params)
            portal_url = api.build_literature_portal_url(search_params)

            await process.log(
                "Sending literature search request to GBIF",
                data={"url": api_url},
            )

            raw_response = await execute_request(api_url)

            status_code = raw_response.get("status_code", 200)
            if status_code != 200:
                await process.log(
                    f"Data retrieval failed with status code {status_code}",
                    data=raw_response,
                )
                await context.reply(
                    f"Literature search failed with status code {status_code}"
                )
                return

            await process.log(f"Data retrieval successful, status code {status_code}")

            page_info = {
                "count": raw_response.get("count"),
                "limit": raw_response.get("limit"),
                "offset": raw_response.get("offset"),
            }

            pagination_message = "API pagination information of the response"
            if page_info.get("count") and page_info.get("count") > (
                (page_info.get("limit") or 0) + (page_info.get("offset") or 0)
            ):
                pagination_message = "Warning: The response is truncated due to pagination and only contains a subset of the literature available on GBIF."
            await process.log(pagination_message, data=page_info)

            artifact_description = await _generate_artifact_description(
                f"User request: {request} "
                f"Identified organisms: {json.dumps(serialize_organisms(expansion_response.organisms))}, "
                f"Search parameters: {json.dumps(serialize_for_log(search_params))}, "
                f"URL: {api_url}"
            )

            await process.create_artifact(
                mimetype="application/json",
                description=artifact_description,
                uris=[api_url],
                metadata={
                    "portal_url": portal_url,
                    "data_source": "GBIF Literature",
                },
            )

            summary = _generate_response_summary(page_info, portal_url)
            await context.reply(summary)

        except Exception as e:
            await process.log(
                "Error during literature search",
                data={
                    "error": str(e),
                    "agent_log_id": AGENT_LOG_ID,
                },
            )
            await context.reply(
                f"I encountered an error while searching for literature: {str(e)}"
            )


def _generate_response_summary(page_info: dict, portal_url: str) -> str:
    count = page_info.get("count") or 0
    if count > 0:
        summary = (
            f"I found {count} publication(s) matching your criteria. "
            f"Showing {page_info.get('limit')} results per page. "
        )
    else:
        summary = "I could not find any publications matching your criteria. "
    summary += f"You can explore the full results in the GBIF literature portal at {portal_url}."
    return summary