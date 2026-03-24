# Response Schema: find_occurrence_records
**Tool:** find_occurrence_records
**Endpoint:** `GET /v1/occurrence/search`
**GBIF Service:** Occurrence Search

---

## Top Level
| Field | Type | Notes |
|-------|------|-------|
| count | int | Total matching records in GBIF — not just the page returned |
| limit | int | Number of records returned in this page |
| offset | int | Offset used for this page |
| endOfRecords | bool | True if no more pages available |
| results | array | Occurrence records for the current page |

---

## Occurrence Record Fields

### Identity
| Field | Type | Notes |
|-------|------|-------|
| gbifID | string | GBIF's unique identifier for this occurrence |
| occurrenceID | string | Original identifier from the data provider |
| taxonKey | int | GBIF backbone taxon key |
| speciesKey | int | Taxon key at species rank |
| genusKey | int | Taxon key at genus rank |
| familyKey | int | Taxon key at family rank |

### Taxonomy
| Field | Type | Notes |
|-------|------|-------|
| scientificName | string | Matched scientific name from GBIF backbone |
| verbatimScientificName | string | Original name as submitted by data provider |
| vernacularName | string | Common name if available |
| taxonRank | string | Rank of matched taxon e.g. SPECIES, GENUS |
| kingdom / phylum / class / order / family / genus / species | string | Full classification hierarchy |

### Location
| Field | Type | Notes |
|-------|------|-------|
| decimalLatitude | float | WGS84 latitude |
| decimalLongitude | float | WGS84 longitude |
| country | string | ISO 2-letter country code e.g. "US" |
| countryCode | string | Same as country |
| stateProvince | string | State or province name |
| locality | string | Specific locality description |
| continent | string | Continent e.g. NORTH_AMERICA |

### Event
| Field | Type | Notes |
|-------|------|-------|
| eventDate | string | ISO 8601 date string e.g. "2021-08-15" |
| year | int | Year of observation |
| month | int | Month of observation |
| day | int | Day of observation |

### Record Provenance
| Field | Type | Notes |
|-------|------|-------|
| basisOfRecord | string | How record was created. Values: HUMAN_OBSERVATION, PRESERVED_SPECIMEN, MACHINE_OBSERVATION, LIVING_SPECIMEN, FOSSIL_SPECIMEN, MATERIAL_SAMPLE |
| datasetKey | string | UUID of the dataset this record belongs to |
| datasetName | string | Name of the dataset |
| publishingOrgKey | string | UUID of the publishing organisation |
| institutionCode | string | Code of the institution holding the specimen |
| collectionCode | string | Collection code within the institution |
| catalogNumber | string | Catalogue number of the specimen |
| recordedBy | string | Observer or collector name |
| identifiedBy | string | Person who identified the taxon |
| license | string | License of the record e.g. CC_BY_4_0 |

### Media
| Field | Type | Notes |
|-------|------|-------|
| media | array | List of media objects attached to this record |
| media[].type | string | Media type e.g. StillImage |
| media[].identifier | string | Direct URL to the media file |

### Data Quality
| Field | Type | Notes |
|-------|------|-------|
| issues | array | GBIF data quality flags e.g. COORDINATE_ROUNDED, TAXON_MATCH_FUZZY |
| hasCoordinate | bool | True if record has valid coordinates |
| hasGeospatialIssues | bool | True if any geospatial issues flagged |

---

## Note
`count` reflects total available records — results are paginated. If `count > limit + offset` the response is truncated. Use portal URL to explore full dataset interactively.
