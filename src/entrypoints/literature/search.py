import uuid
import json

from ichatbio.agent_response import ResponseContext
from ichatbio.types import AgentEntrypoint

from src.gbif.api import GbifApi
from src.gbif.fetch import execute_request
from src.gbif.parser import parse
from src.gbif.resolve_parameters import resolve_names_to_taxonkeys
from src.models.literature import GBIFLiteratureByIdParams, GBIFLiteratureSearchParams
from src.models.validators import (
    LiteratureByIdParamsValidator,
    LiteratureSearchParamsValidator,
)
from src.log import with_logging, logger
from src.utils import (
    serialize_for_log,
    _generate_artifact_description,
    _preprocess_user_request,
    serialize_organisms,
)


# ══════════════════════════════════════════════════════════════════════════════
# find_literature_by_id
# ══════════════════════════════════════════════════════════════════════════════

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
    """
    Retrieves a single literature record by its GBIF UUID.
    """
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

        try:
            await process.log("Querying GBIF", data={"url": api_url})
            raw_response = await execute_request(api_url)
            status_code = raw_response.get("status_code", 200)

            if status_code == 404:
                await context.reply("The provided UUID was not found in GBIF.")
                return

            if status_code != 200:
                await context.reply(f"Request failed with status code {status_code}")
                return

            doi = raw_response.get("identifiers", {}).get("doi")

            await process.log(
                "Record information",
                data={
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
                    "doi": doi,
                },
            )

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
                "Error", data={"error": str(e), "agent_log_id": AGENT_LOG_ID}
            )
            await context.reply(
                f"I encountered an error while retrieving the literature record: {str(e)}"
            )


def _generate_by_id_response_summary(lit_uuid: str, portal_url: str) -> str:
    return (
        f"I have successfully retrieved the literature record with UUID {lit_uuid}. "
        f"You can view the full record in the GBIF portal at {portal_url}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# find_literature
# ══════════════════════════════════════════════════════════════════════════════

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


# Higher taxonomic ranks that should use gbifHigherTaxonKey
HIGHER_TAXON_RANKS = {"family", "order", "class", "phylum", "kingdom"}


@with_logging("find_literature")
async def run_search(context: ResponseContext, request: str):
    """
    Searches for scientific literature that cites or uses GBIF-mediated data.
    Includes preprocessing to extract organisms and resolve them to GBIF taxon keys.
    Uses gbifHigherTaxonKey for family/order/class level queries.
    """
    async with context.begin_process("Searching GBIF Literature") as process:
        AGENT_LOG_ID = f"FIND_LITERATURE_{str(uuid.uuid4())[:6]}"
        logger.info(f"Agent log ID: {AGENT_LOG_ID}")
        await process.log(f"Request received: {request}\n\nParsing request...")

        # ─── Preprocess: Extract organisms from user request ────────────
        expansion_response = await _preprocess_user_request(request)

        await process.log(
            "Expanded request",
            data={
                "original_request": request,
                "identified_organisms": serialize_organisms(
                    expansion_response.organisms
                ),
            },
        )

        expanded_request = (
            f"User request: {request} "
            f"Identified organisms in the request: {json.dumps(serialize_organisms(expansion_response.organisms))}"
        )
        # ─────────────────────────────────────────────────────────────────

        response = await parse(
            expanded_request,
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

        # ─── Resolve organisms to GBIF taxon keys ───────────────────────
        if expansion_response.organisms:
            await process.log(
                f"Resolving {len(expansion_response.organisms)} organism(s) to GBIF taxon keys..."
            )
            taxon_keys, parent_fallback_names = await resolve_names_to_taxonkeys(
                api, expansion_response.organisms, process
            )
            if taxon_keys:
                # Determine if we should use gbifTaxonKey or gbifHigherTaxonKey
                # based on the taxonomic rank of the organisms
                organism_ranks = [
                    org.taxonomic_rank.lower()
                    for org in expansion_response.organisms
                    if org.taxonomic_rank
                ]

                # If any organism is a higher rank, use gbifHigherTaxonKey
                if any(rank in HIGHER_TAXON_RANKS for rank in organism_ranks):
                    existing_keys = search_params.gbifHigherTaxonKey or []
                    merged_keys = list(set(existing_keys + taxon_keys))
                    search_params = search_params.model_copy(
                        update={"gbifHigherTaxonKey": merged_keys}
                    )
                    await process.log(
                        f"Resolved to gbifHigherTaxonKey (higher taxon detected): {merged_keys}",
                        data={"gbifHigherTaxonKey": merged_keys},
                    )
                else:
                    # Species or genus level - use gbifTaxonKey
                    existing_keys = search_params.gbifTaxonKey or []
                    merged_keys = list(set(existing_keys + taxon_keys))
                    search_params = search_params.model_copy(
                        update={"gbifTaxonKey": merged_keys}
                    )
                    await process.log(
                        f"Resolved to gbifTaxonKey: {merged_keys}",
                        data={"gbifTaxonKey": merged_keys},
                    )

                    if parent_fallback_names:
                        existing_q = search_params.q or ""
                        fallback_q = " ".join(parent_fallback_names)
                        new_q = f"{existing_q} {fallback_q}".strip() if existing_q else fallback_q
                        search_params = search_params.model_copy(update={"q": new_q})
                        await process.log(
                            f"Added parent fallback names to q parameter: {fallback_q}"
                        )
            else:
                await process.log(
                    "Could not resolve organisms to taxon keys, will use free text search if q parameter is set"
                )
        # ─────────────────────────────────────────────────────────────────

        await process.log(
            "Final search parameters", data=serialize_for_log(search_params)
        )

        try:
            api_url = api.build_literature_search_url(search_params)
            portal_url = api.build_literature_portal_url(search_params)

            await process.log("Querying GBIF literature", data={"url": api_url})

            raw_response = await execute_request(api_url)
            status_code = raw_response.get("status_code", 200)

            if status_code != 200:
                await context.reply(
                    f"Literature search failed with status code {status_code}"
                )
                return

            count = raw_response.get("count", 0)
            limit = raw_response.get("limit", 20)
            offset = raw_response.get("offset", 0)
            is_truncated = count > (limit + offset)

            await process.log(
                "Results summary",
                data={
                    "total": count,
                    "returned": limit,
                    "truncated": is_truncated,
                },
            )

            # Log preview of top results
            results_preview = []
            for r in raw_response.get("results", [])[:3]:
                doi = r.get("identifiers", {}).get("doi")
                results_preview.append(
                    {
                        "id": r.get("id"),
                        "title": r.get("title"),
                        "year": r.get("year"),
                        "literatureType": r.get("literatureType"),
                        "source": r.get("source"),
                        "authors": [
                            f"{a.get('firstName')} {a.get('lastName')}"
                            for a in r.get("authors", [])[:3]
                        ],
                        "openAccess": r.get("openAccess"),
                        "peerReview": r.get("peerReview"),
                        "doi_url": f"https://doi.org/{doi}" if doi else None,
                    }
                )
            await process.log("Top results", data={"results": results_preview})

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

            summary = _generate_search_response_summary(
                count, limit, is_truncated, portal_url
            )
            await context.reply(summary)

        except Exception as e:
            await process.log(
                "Error", data={"error": str(e), "agent_log_id": AGENT_LOG_ID}
            )
            await context.reply(
                f"I encountered an error while searching for literature: {str(e)}"
            )


def _generate_search_response_summary(
    count: int, limit: int, is_truncated: bool, portal_url: str
) -> str:
    if count > 0:
        summary = f"I found {count} publication(s) matching your criteria. "
        if is_truncated:
            summary += f"Showing top {limit} results. "
    else:
        summary = "I could not find any publications matching your criteria. "
    summary += (
        f"You can explore the full results in the GBIF literature portal at {portal_url}."
    )
    return summary