# Response Schema: find_taxonomic_information
**Tool:** find_taxonomic_information
**Endpoints:** Multiple parallel calls to `/v1/species/{key}`, `/v1/species/{key}/parents`, `/v1/species/{key}/children`, `/v1/species/{key}/synonyms`
**GBIF Service:** Species Detail

---

## Response Structure
The artifact contains a combined object with data from multiple endpoints.

### basic
Core species information — same fields as `find_species_records` single record.

| Field | Type | Notes |
|-------|------|-------|
| key | int | GBIF usage key |
| scientificName | string | Full scientific name with authorship |
| canonicalName | string | Name without authorship |
| rank | string | Taxonomic rank |
| taxonomicStatus | string | ACCEPTED, SYNONYM etc. |
| kingdom / phylum / class / order / family / genus | string | Classification |
| extinct | bool | Extinction status |
| threatStatuses | array | IUCN threat statuses |

### parents
Taxonomic hierarchy from species up to kingdom — ordered from immediate parent to kingdom.

| Field | Type | Notes |
|-------|------|-------|
| key | int | Taxon key of parent |
| scientificName | string | Name of parent taxon |
| rank | string | Rank of parent taxon |

### children
Child taxa (subspecies, varieties etc.) — paginated to 20 by default.

| Field | Type | Notes |
|-------|------|-------|
| key | int | Taxon key of child |
| scientificName | string | Name of child taxon |
| rank | string | Rank of child taxon |
| taxonomicStatus | string | Status of child taxon |

### synonyms
Alternative scientific names for this taxon.

| Field | Type | Notes |
|-------|------|-------|
| key | int | Taxon key of synonym |
| scientificName | string | Synonym name with authorship |
| taxonomicStatus | string | Always SYNONYM |
| accordingTo | string | Source of synonym relationship |

---

## Note
Not all sections are always present — depends on what the user requested. `parents` gives the full classification path. `children` only returns up to 20 — there may be more. Use `key` from basic to run occurrence searches.
