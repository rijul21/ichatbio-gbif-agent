from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import Field

from src.models.base import ProductionBaseModel
from src.enums.common import CountryEnum


class LiteratureTypeEnum(str, Enum):
    """Type of literature publication."""

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
    """
    How the publication relates to GBIF.
    See https://www.gbif.org/faq?question=literature-relevance
    """

    GBIF_USED = "GBIF_USED"          # Makes substantive use of GBIF-mediated data
    GBIF_CITED = "GBIF_CITED"        # Cites GBIF as a data source
    GBIF_DISCUSSED = "GBIF_DISCUSSED"  # Discusses GBIF in context
    GBIF_ACKNOWLEDGED = "GBIF_ACKNOWLEDGED"  # Acknowledges GBIF support
    GBIF_PUBLISHED = "GBIF_PUBLISHED"  # Published by GBIF
    GBIF_AUTHOR = "GBIF_AUTHOR"      # Authored by GBIF staff
    GBIF_MENTIONED = "GBIF_MENTIONED"  # Mentions GBIF

    def __str__(self):
        return self.value


class LiteratureTopicEnum(str, Enum):
    """Topic of the publication."""

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
    """Parameters for GBIF literature search - search publications that cite or use GBIF-mediated data."""

    # Core search
    q: Optional[str] = Field(
        None,
        description="Simple full text search. Use for keywords, author names, or phrases. Wildcards not supported. Only use if none of the specific filters below apply.",
        examples=["coral reefs", "invasive species", "climate change birds"],
    )

    # Publication filters
    literatureType: Optional[List[LiteratureTypeEnum]] = Field(
        None,
        description="Type of publication.",
        examples=[[LiteratureTypeEnum.JOURNAL], [LiteratureTypeEnum.THESIS]],
    )

    relevance: Optional[List[LiteratureRelevanceEnum]] = Field(
        None,
        description="How the publication relates to GBIF. GBIF_USED means substantive use of GBIF data in analysis. GBIF_CITED means GBIF is cited as a source.",
        examples=[[LiteratureRelevanceEnum.GBIF_USED], [LiteratureRelevanceEnum.GBIF_CITED]],
    )

    topics: Optional[List[LiteratureTopicEnum]] = Field(
        None,
        description="Topic(s) of the publication.",
        examples=[[LiteratureTopicEnum.CONSERVATION], [LiteratureTopicEnum.CLIMATE_CHANGE]],
    )

    year: Optional[str] = Field(
        None,
        description="Year of publication. Use a single year (e.g. '2020') or a range with comma (e.g. '2018,2022').",
        examples=["2020", "2018,2022"],
    )

    # Access filters
    peerReview: Optional[bool] = Field(
        None,
        description="Filter to only peer-reviewed publications (true) or non-peer-reviewed (false).",
        examples=[True, False],
    )

    openAccess: Optional[bool] = Field(
        None,
        description="Filter to only open access publications (true) or non-open-access (false).",
        examples=[True, False],
    )

    # Geographic filters
    countriesOfResearcher: Optional[List[CountryEnum]] = Field(
        None,
        description="ISO 2-letter country code of the institution the author is affiliated with.",
        examples=[["US"], ["DE", "FR"]],
    )

    countriesOfCoverage: Optional[List[CountryEnum]] = Field(
        None,
        description="ISO 2-letter country code of the geographic focus of the study.",
        examples=[["BR"], ["AU", "NZ"]],
    )

    # GBIF-specific linkage filters
    gbifDatasetKey: Optional[List[UUID]] = Field(
        None,
        description="UUID of a GBIF dataset referenced in the publication.",
        examples=[["50c9509d-22c7-4a22-a47d-8c48425ef4a7"]],
    )

    publishingOrganizationKey: Optional[UUID] = Field(
        None,
        description="UUID of the publishing organization whose dataset is referenced in the publication.",
        examples=["b542788f-0dc2-4a2b-b652-fceced449591"],
    )

    gbifDownloadKey: Optional[str] = Field(
        None,
        description="A GBIF download key referenced in the publication.",
        examples=["0001005-130906152512535"],
    )

    gbifOccurrenceKey: Optional[int] = Field(
        None,
        description="A specific GBIF occurrence key referenced in the publication.",
        examples=[1258202812],
    )

    gbifTaxonKey: Optional[int] = Field(
        None,
        description="A GBIF taxon key referenced in the publication.",
        examples=[2435098],
    )

    doi: Optional[str] = Field(
        None,
        description="Digital Object Identifier (DOI) of the publication.",
        examples=["10.1038/s41586-019-1573-4"],
    )

    # Journal filters
    journalSource: Optional[str] = Field(
        None,
        description="Name of the journal where the article was published.",
        examples=["Nature", "Science", "Global Ecology and Biogeography"],
    )

    journalPublisher: Optional[str] = Field(
        None,
        description="Name of the journal publisher.",
        examples=["Wiley", "Elsevier", "Springer"],
    )

    # Pagination
    limit: Optional[int] = Field(
        20,
        description="Number of results to return. Maximum is 1000.",
        examples=[20, 100],
    )

    offset: Optional[int] = Field(
        None,
        description="Offset for paginating through results.",
        examples=[0, 20, 100],
    )