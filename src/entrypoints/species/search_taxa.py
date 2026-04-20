from ichatbio.agent_response import ResponseContext, IChatBioAgentProcess
from ichatbio.types import AgentEntrypoint

from src.gbif.api import GbifApi
from src.gbif.fetch import execute_request, execute_multiple_requests
from src.models.entrypoints import GBIFSpeciesSearchParams, GBIFSpeciesTaxonomicParams
from src.enums.species import (
    TaxonomicStatusEnum,
    TaxonomicRankEnum,
    QueryFieldEnum,
)
from src.models.responses.species import NameUsage, PagingResponseNameUsage
from src.log import with_logging, logger
from src.gbif.parser import parse

from pydantic import BaseModel, Field
from typing import List, Optional

from dotenv import load_dotenv
from src.instructor_client import get_client

load_dotenv()


description = f"""
**Use Case:** Use this entrypoint to retrieve taxonomic information (like the full parent hierarchy, child taxa, or synonyms) that matches with a scientificName or taxonKey. It can also be used to find specific identifiers such as taxonKey, kingdomKey, etc in GBIF Backbone Taxonomy.

**Triggers On:** User requests may ask to find, get, or show the "taxonomic information of", "synonyms of", "children of", "parents of", "kingdomKey/taxonKey/classKey...etc" for a species.

**Key Inputs:** Requires the species taxonKey or a scientificName. It also accepts a rank and a qField to narrow down the search results if the user provides a name; Make sure to include the fields in the request.

If only name is provided, it will try to first search for the species usageKey in the GBIF Backbone Taxonomy and then retrieve the taxonomic information. If a taxonKey is provided, it will directly retrieve the taxonomic information.
"""


entrypoint = AgentEntrypoint(
    id="find_taxonomic_information",
    name="Species Taxonomic Information",
    description=description,
    examples=[
        "Get taxonomic information for species with id 5231190",
        "Show taxonomic hierarchy and synonyms for species 2476674",
        "Retrieve taxonomic data for species id 2877951 including children taxa",
    ],
)

GBIF_BACKBONE_DATASET_KEY = "d7dddbf4-2cf0-4f39-9b2a-bb099caae36c"


@with_logging("find_taxonomic_information")
async def run(context: ResponseContext, request: str):
    """
    Executes the species taxonomic information entrypoint. Retrieves comprehensive taxonomic
    information for a specific species using its GBIF identifier.
    """
    async with context.begin_process(
        "Requesting GBIF Species Taxonomic Information"
    ) as process:
        await process.log(
            f"Request received: {request} \n\nGenerating iChatBio for GBIF request parameters..."
        )
        response = await parse(request, entrypoint.id, GBIFSpeciesTaxonomicParams)
        if response.clarification_needed:
            await process.log(f"Clarification needed: {response.clarification_reason}")
            await context.reply(f"{response.clarification_reason}")
            return

        params = response.params
        api = GbifApi()

        await process.log(
            "Generated search parameters",
            data=params.model_dump(exclude_defaults=True),
        )

        if not getattr(params, "key", None) and not getattr(params, "name", None):
            await context.reply(
                "Species id or name is required to retrieve taxonomic information."
            )
            return

        if not getattr(params, "key", None):
            await process.log(
                f"No species id found, searching for species by name: {params.name}"
            )
            species_key = await __search_species_by_name(
                api, request, params.name, params.rank, params.qField, process
            )
            params = params.model_copy(update={"key": species_key})

        urls = api.build_species_taxonomic_urls(params)
        await process.log(f"Generated API URLs: {urls}")

        try:
            await process.log(
                f"Querying GBIF endpoints to gather taxonomic information..."
            )
            results = await execute_multiple_requests(urls)
            failed_endpoints = []
            failed_urls = []
            successful_retrieval = False
            for endpoint_name, result in results.items():
                if isinstance(result, dict) and result.get("error"):
                    await process.log(
                        f"Data retrieval failed for '{endpoint_name}': {result.get('error')}"
                    )
                    failed_endpoints.append(endpoint_name)
                    failed_urls.append(urls.get(endpoint_name, ""))
                else:
                    successful_retrieval = True

            if not successful_retrieval:
                await process.log("Data retrieval failed.")
                await process.create_artifact(
                    mimetype="application/json",
                    description="Taxonomic information could not be retrieved.",
                    uris=failed_urls,
                    metadata={
                        "data_source": "GBIF Species",
                        "key": params.key,
                    },
                )
                await context.reply(f"Taxonomic information could not be retrieved.")
                return

            await process.log(f"Data retrieval successful")

            taxonomic_data = __extract_taxonomic_data(results)

            await process.create_artifact(
                mimetype="application/json",
                description=response.artifact_description,
                uris=[f"https://api.gbif.org/v1/species/{params.key}"],
                metadata={
                    "data_source": "GBIF Species",
                    "key": params.key,
                },
            )

            await process.log(
                "Generating summary for data extracted", data=taxonomic_data
            )

            summary = _generate_response_summary(params.key, taxonomic_data)
            await context.reply(summary)

        except Exception as e:
            await process.log(
                f"Error retrieving taxonomic information",
                data={"error": str(e)},
            )
            await context.reply(f"Failed to retrieve taxonomic information: {str(e)}")


def _generate_response_summary(species_key: int, taxonomic_data: dict) -> str:
    """Generate a summary of the taxonomic information retrieved."""
    summary = f"I have successfully retrieved taxonomic information for species with ID {species_key}. "

    if "basic_info" in taxonomic_data:
        basic = taxonomic_data["basic_info"]
        summary += f"The species '{basic.get('scientific_name', 'Unknown')}' is classified as {basic.get('rank', 'Unknown')} in the {basic.get('family', 'Unknown')} family. "

    if "taxonomic_hierarchy" in taxonomic_data:
        hierarchy_count = len(taxonomic_data["taxonomic_hierarchy"])
        summary += f"Found {hierarchy_count} parent taxa in the taxonomic hierarchy. "

    if "synonyms" in taxonomic_data:
        synonym_count = taxonomic_data["synonyms"].get("count", 0)
        summary += f"Found {synonym_count} synonym records. "

    if "children" in taxonomic_data:
        children_count = taxonomic_data["children"].get("count", 0)
        summary += f"Found {children_count} child taxa. "

    summary += "The detailed taxonomic information has been saved as an artifact."
    return summary


def __extract_taxonomic_data(results: dict) -> dict:
    taxonomic_data = {}

    if "basic" in results and "error" not in results["basic"]:
        try:
            basic = NameUsage(**results["basic"])
            taxonomic_data["basic_info"] = {
                "scientific_name": basic.scientificName,
                "canonical_name": basic.canonicalName,
                "rank": basic.rank,
                "taxonomic_status": basic.taxonomicStatus,
                "kingdom": basic.kingdom,
                "phylum": basic.phylum,
                "class": basic.class_,
                "order": basic.order,
                "family": basic.family,
                "genus": basic.genus,
                "is_extinct": basic.isExtinct,
            }
        except Exception as e:
            logger.error(f"Error parsing basic info {e}; adding raw results")
            taxonomic_data["basic_info"] = results["basic"]

    if "parents" in results and "error" not in results["parents"]:
        try:
            parents = [NameUsage(**parent) for parent in results["parents"]]
            taxonomic_data["taxonomic_hierarchy"] = [
                {
                    "rank": parent.rank,
                    "scientific_name": parent.scientificName,
                    "usage_key": parent.key,
                }
                for parent in parents
            ]
        except Exception as e:
            logger.error(f"Error parsing parents {e}; adding raw results")
            taxonomic_data["taxonomic_hierarchy"] = results["parents"]

    if "synonyms" in results and "error" not in results["synonyms"]:
        try:
            synonyms_response = PagingResponseNameUsage(**results["synonyms"])
            taxonomic_data["synonyms"] = {
                "count": synonyms_response.count,
                "results": [
                    {
                        "scientific_name": item.scientificName,
                        "taxonomic_status": item.taxonomicStatus,
                        "usage_key": item.key,
                    }
                    for item in synonyms_response.results
                ],
            }
        except Exception as e:
            logger.error(f"Error parsing synonyms {e}; adding raw results")
            taxonomic_data["synonyms"] = results["synonyms"]

    if "children" in results and "error" not in results["children"]:
        try:
            children_response = PagingResponseNameUsage(**results["children"])
            taxonomic_data["children"] = {
                "count": children_response.count,
                "results": [
                    {
                        "scientific_name": item.scientificName,
                        "rank": item.rank,
                        "usage_key": item.key,
                    }
                    for item in children_response.results
                ],
            }
        except Exception as e:
            logger.error(f"Error parsing children {e}; adding raw results")
            taxonomic_data["children"] = results["children"]

    return taxonomic_data


class SpeciesMatch(BaseModel):
    key: int
    scientificName: str
    canonicalName: Optional[str] = None
    rank: Optional[str] = None
    kingdom: Optional[str] = None
    phylum: Optional[str] = None
    class_: Optional[str] = Field(None, alias="class")
    order: Optional[str] = None
    family: Optional[str] = None
    genus: Optional[str] = None
    isExtinct: Optional[bool] = None


async def __search_species_by_name(
    api: GbifApi,
    user_query: str,
    name: str,
    rank: Optional[TaxonomicRankEnum],
    qField: Optional[QueryFieldEnum],
    process: IChatBioAgentProcess,
) -> int:
    await process.log(f"Searching for species by name: {name}")
    # Create the search params for species using the GBIF Backbone Dataset Key at once
    params = GBIFSpeciesSearchParams(
        q=name,
        status=TaxonomicStatusEnum.ACCEPTED,
        datasetKey=GBIF_BACKBONE_DATASET_KEY,
        rank=rank,
        qField=qField,
    )

    url = api.build_species_search_url(params)

    await process.log(f"Searching for species in the GBIF Backbone Taxonomy: {url}")

    try:
        raw_response = await execute_request(url)
        records = raw_response.get("results", [])
        count = raw_response.get("count", 0)
        await process.log(
            f"Found {count} matches for species name: {name}, working with the first {len(records)}"
        )

        species_matches: List[SpeciesMatch] = []
        for r in records:
            species_matches.append(
                SpeciesMatch(
                    key=r.get("key"),
                    scientificName=r.get("scientificName"),
                    canonicalName=r.get("canonicalName"),
                    rank=r.get("rank"),
                    kingdom=r.get("kingdom"),
                    phylum=r.get("phylum"),
                    class_=r.get("class"),
                    order=r.get("order"),
                    family=r.get("family"),
                    genus=r.get("genus"),
                    isExtinct=r.get("isExtinct"),
                )
            )

        if not species_matches:
            raise ValueError(f"No species matches found for name: {name}")

        await process.create_artifact(
            mimetype="application/json",
            description=f"Species matches for provided name: {name}",
            uris=[url],
            metadata={
                "data_source": "GBIF Species Matches",
            },
        )

        best_match = await __find_best_match(species_matches, user_query)
        await process.log(f"Selected best match: {best_match.model_dump_json()}")
        return best_match.key

    except Exception as e:
        await process.log(
            f"Error searching for species by name",
            data={"error": str(e), "species_name": name},
        )
        raise


async def __find_best_match(
    species_matches: List[SpeciesMatch], user_query: str
) -> SpeciesMatch:

    client = await get_client()

    response = await client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a helpful biodiversity researcher assistant that finds the best match for a species name for the user query. You will be given a user query and a dictionary of species keys and details. You will need to return the best match.",
            },
            {
                "role": "user",
                "content": f"User query: {user_query}\n\nSpecies name to key: {species_matches}",
            },
        ],
        response_model=SpeciesMatch,
    )

    return response
