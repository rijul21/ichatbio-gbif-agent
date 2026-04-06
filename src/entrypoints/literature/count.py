import uuid
import json

from ichatbio.agent_response import ResponseContext
from ichatbio.types import AgentEntrypoint

from src.gbif.api import GbifApi
from src.gbif.fetch import execute_request
from src.gbif.parser import parse
from src.gbif.resolve_parameters import resolve_names_to_taxonkeys
from src.models.literature import GBIFLiteratureFacetsParams
from src.models.validators import LiteratureFacetsParamsValidator
from src.log import with_logging, logger
from src.utils import (
    serialize_for_log,
    _generate_artifact_description,
    _preprocess_user_request,
    serialize_organisms,
)


description = """
**Use Case:** Use this entrypoint to get statistical counts and breakdowns of GBIF literature data using facets (aggregation).

**Triggers On:** User requests that ask "how many papers", "count of publications", "breakdown of literature by", "number of articles per year", "publications by topic", or any statistical summary of literature data.

**Key Inputs:** Requires at least one facet field to aggregate by (e.g., year, topics, relevance, countriesOfResearcher, literatureType). Can be combined with filters like topics, year range, peerReview, openAccess, etc.

**Limitations:** Returns aggregated counts, not individual publication records. For listing actual papers, use find_literature instead.
"""

entrypoint = AgentEntrypoint(
    id="count_literature_records",
    description=description,
    parameters=None,
)


@with_logging("count_literature_records")
async def run(context: ResponseContext, request: str):
    """
    Executes the literature facet/count entrypoint. Aggregates literature data
    by specified facet fields and returns counts.
    """
    async with context.begin_process("Counting GBIF Literature Records") as process:
        AGENT_LOG_ID = f"COUNT_LITERATURE_{str(uuid.uuid4())[:6]}"
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
            entrypoint.id,
            LiteratureFacetsParamsValidator,
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
            taxon_keys = await resolve_names_to_taxonkeys(
                api, expansion_response.organisms, process
            )
            if taxon_keys:
                # Determine if we should use gbifTaxonKey or gbifHigherTaxonKey
                # based on the taxonomic rank of the organisms
                higher_ranks = {"family", "order", "class", "phylum", "kingdom"}
                organism_ranks = [
                    org.taxonomic_rank.lower()
                    for org in expansion_response.organisms
                    if org.taxonomic_rank
                ]

                # If any organism is a higher rank, use gbifHigherTaxonKey
                if any(rank in higher_ranks for rank in organism_ranks):
                    existing_keys = search_params.gbifHigherTaxonKey or []
                    merged_keys = list(set(existing_keys + taxon_keys))
                    search_params = search_params.model_copy(
                        update={"gbifHigherTaxonKey": merged_keys}
                    )
                    await process.log(
                        f"Resolved to gbifHigherTaxonKey: {merged_keys}",
                        data={"gbifHigherTaxonKey": merged_keys},
                    )
                else:
                    existing_keys = search_params.gbifTaxonKey or []
                    merged_keys = list(set(existing_keys + taxon_keys))
                    search_params = search_params.model_copy(
                        update={"gbifTaxonKey": merged_keys}
                    )
                    await process.log(
                        f"Resolved to gbifTaxonKey: {merged_keys}",
                        data={"gbifTaxonKey": merged_keys},
                    )
            else:
                await process.log(
                    "Could not resolve organisms to taxon keys, proceeding without taxon filter"
                )
        # ─────────────────────────────────────────────────────────────────

        # Set limit to 0 for facet-only queries
        search_params = search_params.model_copy(update={"limit": 0})

        await process.log(
            "Final search parameters", data=serialize_for_log(search_params)
        )

        try:
            api_url = api.build_literature_search_url(search_params)
            portal_url = api.build_literature_portal_url(search_params)

            await process.log("Querying GBIF literature facets", data={"url": api_url})

            raw_response = await execute_request(api_url)
            status_code = raw_response.get("status_code", 200)

            if status_code != 200:
                await context.reply(
                    f"Literature count failed with status code {status_code}"
                )
                return

            total_count = raw_response.get("count", 0)
            facets = raw_response.get("facets", [])

            await process.log(
                "Facet results",
                data={
                    "total_count": total_count,
                    "facets_returned": len(facets),
                },
            )

            # Log facet breakdown
            facet_summary = {}
            for facet in facets:
                field = facet.get("field", "unknown")
                counts = facet.get("counts", [])
                facet_summary[field] = [
                    {"name": c.get("name"), "count": c.get("count")}
                    for c in counts[:10]  # Top 10 per facet
                ]
            await process.log("Facet breakdown (top 10 per field)", data=facet_summary)

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
                    "total_count": total_count,
                },
            )

            summary = _generate_count_response_summary(
                total_count, facets, portal_url
            )
            await context.reply(summary)

        except Exception as e:
            await process.log(
                "Error", data={"error": str(e), "agent_log_id": AGENT_LOG_ID}
            )
            await context.reply(
                f"I encountered an error while counting literature records: {str(e)}"
            )


def _generate_count_response_summary(
    total_count: int, facets: list, portal_url: str
) -> str:
    """Generate a human-readable summary of facet results."""
    if total_count == 0:
        return (
            "I could not find any publications matching your criteria. "
            f"You can explore the GBIF literature portal at {portal_url}."
        )

    summary = f"I found {total_count} publication(s) matching your criteria. "

    # Add facet breakdown to summary
    for facet in facets:
        field = facet.get("field", "unknown")
        counts = facet.get("counts", [])

        if counts:
            # Format field name for readability
            field_name = field.replace("_", " ").replace("Of", " of ")

            # Show top 5 values
            top_values = counts[:5]
            breakdown_parts = [
                f"{c.get('name')}: {c.get('count')}" for c in top_values
            ]
            breakdown = ", ".join(breakdown_parts)

            if len(counts) > 5:
                summary += f"\n\nBreakdown by {field_name} (top 5): {breakdown}, and {len(counts) - 5} more."
            else:
                summary += f"\n\nBreakdown by {field_name}: {breakdown}."

    summary += f"\n\nYou can explore the full results in the GBIF literature portal at {portal_url}."
    return summary