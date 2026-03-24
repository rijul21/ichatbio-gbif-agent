# Response Schema: count_occurrence_records
**Tool:** count_occurrence_records
**Endpoint:** `GET /v1/occurrence/search` (with facet parameters)
**GBIF Service:** Occurrence Facets

---

## Top Level
| Field | Type | Notes |
|-------|------|-------|
| count | int | Total matching records across all filters |
| limit | int | Always 0 for facet-only queries |
| offset | int | Offset used |
| facets | array | One entry per requested facet field |

---

## Facet Entry
| Field | Type | Notes |
|-------|------|-------|
| field | string | The facet field name e.g. "COUNTRY", "SPECIES_KEY", "YEAR" |
| counts | array | List of value + count pairs |

## Per counts Item
| Field | Type | Notes |
|-------|------|-------|
| name | string | The value for this facet bucket e.g. "US", "2021" |
| count | int | Number of occurrence records with this value |

---

## Supported Facet Fields
| Facet | Returns |
|-------|---------|
| country | Breakdown by country (ISO codes) |
| year | Breakdown by year |
| basisOfRecord | Breakdown by record type |
| speciesKey | Top species by record count |
| genusKey | Top genera by record count |
| familyKey | Top families by record count |
| kingdom | Breakdown by kingdom |
| datasetKey | Breakdown by dataset |
| stateProvince | Breakdown by state/province |
| continent | Breakdown by continent |

---

## Note
Facet keys (speciesKey, genusKey etc.) are resolved to scientific names by the agent before returning to the user. `count` at the top level is the total records matching the filters — use this for summary statistics.
