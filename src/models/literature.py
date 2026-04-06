from pydantic import Field
from uuid import UUID
from typing import Optional, List
from enum import Enum
from src.models.base import ProductionBaseModel
from src.enums.common import CountryEnum


class GBIFLiteratureByIdParams(ProductionBaseModel):
    uuid: UUID = Field(
        ...,
        description="UUID of the literature item to retrieve.",
        examples=["83a00190-7038-3970-a7e8-5e5563c40e37"],
    )


class LiteratureTypeEnum(str, Enum):
    JOURNAL = "JOURNAL"
    BOOK = "BOOK"
    BOOK_SECTION = "BOOK_SECTION"
    WORKING_PAPER = "WORKING_PAPER"
    REPORT = "REPORT"
    THESIS = "THESIS"
    CONFERENCE_PROCEEDINGS = "CONFERENCE_PROCEEDINGS"
    WEB_PAGE = "WEB_PAGE"
    GENERIC = "GENERIC"

    def __str__(self):
        return self.value


class LiteratureRelevanceEnum(str, Enum):
    GBIF_USED = "GBIF_USED"
    GBIF_CITED = "GBIF_CITED"
    GBIF_DISCUSSED = "GBIF_DISCUSSED"
    GBIF_PRIMARY = "GBIF_PRIMARY"
    GBIF_ACKNOWLEDGED = "GBIF_ACKNOWLEDGED"
    GBIF_PUBLISHED = "GBIF_PUBLISHED"
    GBIF_AUTHOR = "GBIF_AUTHOR"
    GBIF_MENTIONED = "GBIF_MENTIONED"
    GBIF_FUNDED = "GBIF_FUNDED"

    def __str__(self):
        return self.value


class LiteratureTopicEnum(str, Enum):
    AGRICULTURE = "AGRICULTURE"
    ALIEN_SPECIES = "ALIEN_SPECIES"
    BEHAVIOUR = "BEHAVIOUR"
    BIODIVERSITY_SCIENCE = "BIODIVERSITY_SCIENCE"
    BIOGEOGRAPHY = "BIOGEOGRAPHY"
    CITIZEN_SCIENCE = "CITIZEN_SCIENCE"
    CLIMATE_CHANGE = "CLIMATE_CHANGE"
    COLLECTIONS = "COLLECTIONS"
    CONSERVATION = "CONSERVATION"
    DATA_MANAGEMENT = "DATA_MANAGEMENT"
    DATA_PAPER = "DATA_PAPER"
    ECOLOGY = "ECOLOGY"
    ECOSYSTEM_SERVICES = "ECOSYSTEM_SERVICES"
    EVOLUTION = "EVOLUTION"
    FRESHWATER = "FRESHWATER"
    FUNGAL_DIVERSITY = "FUNGAL_DIVERSITY"
    GENETICS = "GENETICS"
    HUMAN_HEALTH = "HUMAN_HEALTH"
    INVASIVES = "INVASIVES"
    MARINE = "MARINE"
    METHODOLOGY = "METHODOLOGY"
    MICROBIAL_DIVERSITY = "MICROBIAL_DIVERSITY"
    PHYLOGENETICS = "PHYLOGENETICS"
    PLANT_PATHOLOGY = "PLANT_PATHOLOGY"
    REMOTE_SENSING = "REMOTE_SENSING"
    SPECIES_DISTRIBUTIONS = "SPECIES_DISTRIBUTIONS"
    TAXONOMY = "TAXONOMY"

    def __str__(self):
        return self.value


class GBIFLiteratureSearchParams(ProductionBaseModel):
    q: Optional[str] = Field(
        None,
        description="Free text search across title, abstract and keywords. Use plain natural language — do not substitute scientific names or codes.",
        examples=["coral reef biodiversity", "climate change birds"],
    )
    literatureType: Optional[List[LiteratureTypeEnum]] = Field(
        None,
        description="Type of publication.",
        examples=[["JOURNAL"], ["THESIS"]],
    )
    relevance: Optional[List[LiteratureRelevanceEnum]] = Field(
        None,
        description="How the publication relates to GBIF.",
        examples=[["GBIF_USED"], ["GBIF_CITED"]],
    )
    topics: Optional[List[LiteratureTopicEnum]] = Field(
        None,
        description="Topic of the publication.",
        examples=[["CONSERVATION"], ["CLIMATE_CHANGE"]],
    )
    year: Optional[str] = Field(
        None,
        description="Publication year or range. Single year e.g. '2020' or range e.g. '2018,2022'.",
        examples=["2020", "2018,2022"],
    )
    peerReview: Optional[bool] = Field(
        None,
        description="Filter to peer-reviewed (true) or non-peer-reviewed (false) publications.",
    )
    openAccess: Optional[bool] = Field(
        None,
        description="Filter to open access (true) or non-open-access (false) publications.",
    )
    countriesOfResearcher: Optional[List[CountryEnum]] = Field(
        None,
        description="ISO 2-letter country code of the author's institution.",
        examples=[["US"], ["DE", "FR"]],
    )
    countriesOfCoverage: Optional[List[CountryEnum]] = Field(
        None,
        description="ISO 2-letter country code of the geographic focus of the study.",
        examples=[["BR"], ["AU"]],
    )
    source: Optional[str] = Field(
        None,
        description="Journal name where the article was published.",
        examples=["Nature", "Science"],
    )
    publisher: Optional[str] = Field(
        None,
        description="Publisher name.",
        examples=["Wiley", "Elsevier"],
    )
    doi: Optional[str] = Field(
        None,
        description="Digital Object Identifier of the publication.",
        examples=["10.1038/s41586-019-1573-4"],
    )
    gbifTaxonKey: Optional[List[int]] = Field(
        None,
        description="GBIF backbone taxon key(s) that are the focus of the paper.",
        examples=[[2435098]],
    )
    gbifDatasetKey: Optional[List[UUID]] = Field(
        None,
        description="UUID of a GBIF dataset referenced in the publication.",
        examples=[["50c9509d-22c7-4a22-a47d-8c48425ef4a7"]],
    )
    language: Optional[str] = Field(
        None,
        description="Language of publication as ISO 639-2 code.",
        examples=["eng", "fra", "deu"],
    )
    limit: Optional[int] = Field(
        20,
        description="Number of results to return.",
    )
    offset: Optional[int] = Field(
        None,
        description="Offset for pagination.",
    )


class GBIFLiteratureFacetsParams(GBIFLiteratureSearchParams):
    facet: Optional[List[str]] = Field(
        None,
        description="Fields to facet by (e.g. 'year', 'topics', 'relevance', 'literatureType', 'countriesOfResearcher', 'countriesOfCoverage').",
        examples=[["year"], ["topics", "relevance"]],
    )
    facetMincount: Optional[int] = Field(
        None,
        description="Minimum count for a facet value to be included in results.",
        examples=[1, 10],
    )
    facetMultiselect: Optional[bool] = Field(
        None,
        description="If true, facet counts are not filtered by the facet parameter.",
    )