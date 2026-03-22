import uuid
import json

from ichatbio.agent_response import ResponseContext
from ichatbio.types import AgentEntrypoint

from src.gbif.api import GbifApi
from src.gbif.fetch import execute_request
from src.gbif.parser import parse
from src.models.literature import GBIFLiteratureByIdParams, GBIFLiteratureSearchParams
from src.models.validators import LiteratureByIdParamsValidator, LiteratureSearchParamsValidator
from src.log import with_logging, logger
from src.utils import serialize_for_log, _generate_artifact_description


# ── find_literature_by_id ──────────────────────────────────────────────────

by_id_description = """
**Use Case:** Use this entrypoint to retrieve a single literature item by its GBIF UUID.

**Triggers On:** User requests to "find literature by ID", "look up paper", or "get details for literature" when a specific GBIF UUID is provided.

**Key Inputs:** Requires a single GBIF literature UUID.

**Limitations:** Only works with a valid GBIF literature UUID. Cannot be used for general searches.
"""

by_id_entrypoint = AgentEntrypoint(
    id="find_literature_by_id",
    description=by_id_description,
    parameters=None,
)


@with_logging("find_literature_by_id")
async def run(context: ResponseContext, request: str):
    async with context.begin_process("Retrieving GBIF Literature by ID") as process:
        AGENT_LOG_ID = f"FIND_LITERATURE_BY_ID_{str(uuid.uuid4())[:6]}"
        logger.info(f"Agent log ID: {AGENT_LOG_ID}")
        await process.log(f"Request received: {request}\n\nParsing request...")

        response = await parse(
            request,
            by_id_entrypoint.id,
            LiteratureByIdParamsValidator,
        )

        if response.clarification_needed:
            await process.log(f"Clarification needed: {response.clarification_reason}")
            await context.reply(response.clarification_reason)
            return

        params = response.params
        artifact_desc = response.artifact_description

        await process.log(
            "Generated parameters",
            data=params.model_dump(exclude_defaults=True),
        )

        api = GbifApi()
        api_url = api.build_literature_by_id_url(params)
        await process.log(f"Constructed API URL: {api_url}")

        try:
            await process.log("Querying GBIF for literature record...")
            raw_response = await execute_request(api_url)
            status_code = raw_response.get("status_code", 200)

            if status_code == 404:
                await process.log("Literature UUID not found", data=raw_response)
                await context.reply("The provided UUID is not valid or was not found in GBIF.")
                return

            if status_code != 200:
                await process.log(
                    f"Data retrieval failed with status code {status_code}",
                    data=raw_response,
                )
                await context.reply(f"Data retrieval failed with status code {status_code}")
                return

            await process.log(f"Data retrieval successful, status code {status_code}")

            subset_response = {
                "id": raw_response.get("id"),
                "title": raw_response.get("title"),
                "authors": raw_response.get("authors"),
                "year": raw_response.get("year"),
                "literatureType": raw_response.get("literatureType"),
                "source": raw_response.get("source"),
                "publisher": raw_response.get("publisher"),
                "openAccess": raw_response.get("openAccess"),
                "peerReview": raw_response.get("peerReview"),
                "relevance": raw_response.get("relevance"),
                "topics": raw_response.get("topics"),
                "doi": raw_response.get("identifiers", {}).get("doi"),
            }
            await process.log("Record information", data=subset_response)

            portal_url = f"https://www.gbif.org/literature/{params.uuid}"

            await process.create_artifact(
                mimetype="application/json",
                description=artifact_desc,
                uris=[api_url],
                metadata={
                    "portal_url": portal_url,
                    "data_source": "GBIF Literature",
                },
            )

            doi = raw_response.get("identifiers", {}).get("doi")
            
            if doi:
                await process.create_artifact(
                    mimetype="text/html",
                    description=f"Full paper: {raw_response.get('title')}",
                    uris=[f"https://doi.org/{doi}"],
                    metadata={
                        "data_source": "External Publisher",
                    },
                )

            summary = _generate_by_id_response_summary(params.uuid, portal_url)
            await context.reply(summary)

        except Exception as e:
            await process.log(
                "Error during literature retrieval",
                data={"error": str(e), "agent_log_id": AGENT_LOG_ID},
            )
            await context.reply(
                f"I encountered an error while retrieving the literature record: {str(e)}"
            )


def _generate_by_id_response_summary(lit_uuid: str, portal_url: str) -> str:
    return (
        f"I have successfully retrieved the literature record with UUID {lit_uuid}. "
        f"You can view the full record in the GBIF portal at {portal_url}."
    )


# ── find_literature ────────────────────────────────────────────────────────

search_description = """
**Use Case:** Use this entrypoint to search for scientific literature that cites or uses GBIF-mediated biodiversity data.

**Triggers On:** User requests to "find papers", "search for publications", "show literature", "find studies", "find research about", or "find articles" related to biodiversity topics.

**Key Inputs:** Accepts free-text search (q), publication type, relevance to GBIF, year or year range, topics, peer-review status, open access status, country of researcher, country of coverage, journal name, publisher, DOI, and taxon key.

**Limitations:** Only searches literature indexed by GBIF. Does not search all scientific literature.
"""

search_entrypoint = AgentEntrypoint(
    id="find_literature",
    description=search_description,
    parameters=None,
)


@with_logging("find_literature")
async def run_search(context: ResponseContext, request: str):
    async with context.begin_process("Searching GBIF Literature") as process:
        AGENT_LOG_ID = f"FIND_LITERATURE_{str(uuid.uuid4())[:6]}"
        logger.info(f"Agent log ID: {AGENT_LOG_ID}")
        await process.log(f"Request received: {request}\n\nParsing request...")

        response = await parse(
            request,
            search_entrypoint.id,
            LiteratureSearchParamsValidator,
        )
        await process.log("Parameter parsing plan", data={"plan": response.plan})

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
                await context.reply(f"Literature search failed with status code {status_code}")
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

            results_preview = []
            for r in raw_response.get("results", [])[:3]:
                results_preview.append({
                    "id": r.get("id"),
                    "title": r.get("title"),
                    "year": r.get("year"),
                    "literatureType": r.get("literatureType"),
                    "source": r.get("source"),
                    "authors": [f"{a.get('firstName')} {a.get('lastName')}" for a in r.get("authors", [])[:3]],
                    "openAccess": r.get("openAccess"),
                    "peerReview": r.get("peerReview"),
                    "doi": r.get("identifiers", {}).get("doi"),
                })
            await process.log("Top results preview", data={"results": results_preview})

            artifact_description = await _generate_artifact_description(
                f"User request: {request} "
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

            summary = _generate_search_response_summary(page_info, portal_url)
            await context.reply(summary)

        except Exception as e:
            await process.log(
                "Error during literature search",
                data={"error": str(e), "agent_log_id": AGENT_LOG_ID},
            )
            await context.reply(
                f"I encountered an error while searching for literature: {str(e)}"
            )


def _generate_search_response_summary(page_info: dict, portal_url: str) -> str:
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