# Response Schema: find_datasets
**Tool:** find_datasets
**Endpoint:** `GET /v1/dataset/search`
**GBIF Service:** Registry — Dataset Search

---

## Top Level
| Field | Type | Notes |
|-------|------|-------|
| count | int | Total matching datasets |
| limit | int | Number of datasets returned |
| offset | int | Offset used |
| results | array | Dataset records |

---

## Dataset Record Fields

### Identity
| Field | Type | Notes |
|-------|------|-------|
| key | string | UUID of the dataset — use as datasetKey in occurrence/literature searches |
| doi | string | DOI of the dataset if available |

### Metadata
| Field | Type | Notes |
|-------|------|-------|
| title | string | Dataset title |
| description | string | Dataset description |
| type | string | Dataset type — OCCURRENCE, CHECKLIST, METADATA, SAMPLING_EVENT |
| subtype | string | More specific type e.g. SPECIMEN, OBSERVATION |
| license | string | License of the dataset e.g. CC_BY_4_0 |
| language | string | Language of the dataset |
| citation | object | Citation information for the dataset |

### Organisation
| Field | Type | Notes |
|-------|------|-------|
| publishingOrganizationKey | string | UUID of the publishing organisation |
| publishingOrganizationTitle | string | Name of the publishing organisation |
| publishingCountry | string | ISO 2-letter country code of publisher |
| hostingOrganizationKey | string | UUID of the hosting organisation |
| installationKey | string | UUID of the installation serving the data |

### Coverage
| Field | Type | Notes |
|-------|------|-------|
| geographicCoverages | array | Geographic areas covered by this dataset |
| taxonomicCoverages | array | Taxa covered by this dataset |
| temporalCoverages | array | Time periods covered by this dataset |

### Statistics
| Field | Type | Notes |
|-------|------|-------|
| recordCount | int | Number of records in this dataset |
| nameUsagesCount | int | Number of name usages (for checklists) |

---

## Note
`key` is the dataset UUID — use it as `datasetKey` in occurrence searches to filter records from a specific dataset, or in literature searches to find papers that used this dataset.
