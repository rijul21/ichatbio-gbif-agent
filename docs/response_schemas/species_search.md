# Response Schema: find_species_records
**Tool:** find_species_records
**Endpoint:** `GET /v1/species/search`
**GBIF Service:** Species Search

---

## Top Level
| Field | Type | Notes |
|-------|------|-------|
| count | int | Total matching name usages |
| limit | int | Number of records returned |
| offset | int | Offset used |
| results | array | Species/taxon records |

---

## Species Record Fields

### Identity
| Field | Type | Notes |
|-------|------|-------|
| key | int | GBIF usage key — use this as taxonKey in occurrence searches |
| nubKey | int | GBIF backbone key — use for cross-dataset matching |
| datasetKey | string | UUID of the checklist this name comes from |

### Name
| Field | Type | Notes |
|-------|------|-------|
| scientificName | string | Full scientific name with authorship |
| canonicalName | string | Scientific name without authorship |
| vernacularName | string | Common name if available |
| authorship | string | Authorship of the name |
| nameType | string | e.g. SCIENTIFIC, HYBRID, INFORMAL |

### Taxonomy
| Field | Type | Notes |
|-------|------|-------|
| rank | string | Taxonomic rank e.g. SPECIES, GENUS, FAMILY |
| taxonomicStatus | string | ACCEPTED, SYNONYM, DOUBTFUL etc. |
| kingdom / phylum / class / order / family / genus / species | string | Full classification |
| kingdomKey / phylumKey / classKey / orderKey / familyKey / genusKey / speciesKey | int | Taxon keys for each rank — use for filtering occurrence searches |

### Status
| Field | Type | Notes |
|-------|------|-------|
| extinct | bool | True if taxon is extinct |
| threatStatuses | array | IUCN threat status values |
| habitats | array | Habitat types e.g. MARINE, FRESHWATER, TERRESTRIAL |

---

## Note
`key` is the most important field — pass it as `taxonKey` to occurrence searches for best performance. `taxonomicStatus=ACCEPTED` means this is the accepted name in GBIF backbone.
