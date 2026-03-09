import uuid

from ichatbio.agent_response import ResponseContext
from ichatbio.types import AgentEntrypoint

from src.gbif.api import GbifApi
from src.gbif.fetch import execute_request
from src.gbif.parser import parse
from src.models.literature import GBIFLiteratureByIdParams
from src.models.validators import LiteratureByIdParamsValidator
from src.log import with_logging, logger


description = """
**Use Case:** Use this entrypoint to retrieve a single literature item by its GBIF UUID.

**Triggers On:** User requests to "find literature by ID", "look up paper", or "get details for literature" when a specific GBIF UUID is provided.

**Key Inputs:** Requires a single GBIF literature UUID.

**Limitations:** Only works with a valid GBIF literature UUID. Cannot be used for general searches.
"""

entrypoint = AgentEntrypoint(
    id="find_literature_by_id",
    description=description,
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
            entrypoint.id,
            LiteratureByIdParamsValidator,
        )

        if response.clarification_needed:
            await process.log(f"Clarification needed: {response.clarification_reason}")
            await context.reply(response.clarification_reason)
            return

        params = response.params
        description = response.artifact_description

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
                description=description,
                uris=[api_url],
                metadata={
                    "portal_url": portal_url,
                    "data_source": "GBIF Literature",
                },
            )

            summary = _generate_response_summary(params.uuid, portal_url)
            await context.reply(summary)

        except Exception as e:
            await process.log(
                "Error during literature retrieval",
                data={"error": str(e), "agent_log_id": AGENT_LOG_ID},
            )
            await context.reply(
                f"I encountered an error while retrieving the literature record: {str(e)}"
            )


def _generate_response_summary(lit_uuid: str, portal_url: str) -> str:
    return (
        f"I have successfully retrieved the literature record with UUID {lit_uuid}. "
        f"You can view the full record in the GBIF portal at {portal_url}."
    )