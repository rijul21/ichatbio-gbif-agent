# Response Schema: find_literature
**Tool:** find_literature
**Endpoint:** `GET /v1/literature/search`
**GBIF Service:** Literature Search

---

## Top Level
| Field | Type | Notes |
|-------|------|-------|
| count | int | Total matching publications |
| limit | int | Number of records returned |
| offset | int | Offset used |
| endOfRecords | bool | True if no more pages |
| results | array | Literature records |

---

## Literature Record Fields

### Identity
| Field | Type | Notes |
|-------|------|-------|
| id | string | GBIF UUID for this literature record — use with find_literature_by_id |
| identifiers.doi | string | DOI of the publication — construct full URL as https://doi.org/{doi} |

### Bibliographic
| Field | Type | Notes |
|-------|------|-------|
| title | string | Publication title |
| abstract | string | Abstract of the publication |
| authors | array | List of {firstName, lastName} objects |
| year | int | Year of publication |
| month | int | Month of publication |
| published | string | Full ISO 8601 publication date |
| source | string | Journal name where published |
| publisher | string | Publisher name |
| keywords | array | Author-supplied keywords |
| language | string | ISO 639-2 language code e.g. "eng" |
| websites | array | Direct URLs to the publication |

### Access
| Field | Type | Notes |
|-------|------|-------|
| openAccess | bool | True if freely available — use doi URL to access full text |
| peerReview | bool | True if peer reviewed |
| literatureType | string | JOURNAL, BOOK, THESIS, REPORT, WORKING_PAPER etc. |

### GBIF Relevance
| Field | Type | Notes |
|-------|------|-------|
| relevance | array | How paper relates to GBIF — GBIF_USED (used GBIF data), GBIF_CITED, GBIF_DISCUSSED etc. |
| topics | array | Subject topics — CONSERVATION, ECOLOGY, CLIMATE_CHANGE, SPECIES_DISTRIBUTIONS etc. |
| citationType | string | How GBIF is cited e.g. "DOI", "generic" |

### GBIF Linkages
| Field | Type | Notes |
|-------|------|-------|
| gbifTaxonKey | array | Taxon keys of species that are the focus of the paper |
| gbifHigherTaxonKey | array | Parent taxon keys |
| gbifDownloadKey | array | GBIF download keys used in this paper |
| gbifDatasetKey | array | Dataset UUIDs referenced in this paper |
| gbifNetworkKey | array | GBIF network UUIDs referenced |
| countriesOfCoverage | array | ISO 2-letter codes of countries the study covers |
| countriesOfResearcher | array | ISO 2-letter codes of author institution countries |

---

## Note
`id` is the GBIF UUID — pass it to `find_literature_by_id` to get full details and a direct paper link artifact. If `openAccess=true`, construct `https://doi.org/{doi}` for free full text access.
