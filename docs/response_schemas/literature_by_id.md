# Response Schema: find_literature_by_id
**Tool:** find_literature_by_id
**Endpoint:** `GET /v1/literature/{uuid}`
**GBIF Service:** Literature Detail

---

## Response
Single literature record — same fields as `find_literature` results but for one specific paper.

## Key Fields
| Field | Type | Notes |
|-------|------|-------|
| id | string | GBIF UUID — same as the ID used to fetch this record |
| title | string | Publication title |
| abstract | string | Full abstract |
| authors | array | List of {firstName, lastName} objects |
| year | int | Publication year |
| source | string | Journal name |
| publisher | string | Publisher name |
| openAccess | bool | True if freely available |
| peerReview | bool | True if peer reviewed |
| literatureType | string | Publication type |
| relevance | array | How paper relates to GBIF |
| topics | array | Subject topics |
| identifiers.doi | string | DOI — agent constructs https://doi.org/{doi} as full paper artifact |
| websites | array | Direct URLs to the publication |
| keywords | array | Author keywords |
| gbifDownloadKey | array | GBIF downloads used in this paper |
| gbifTaxonKey | array | Taxa that are the focus of this paper |
| countriesOfCoverage | array | Countries the study covers |
| countriesOfResearcher | array | Countries of author institutions |

---

## Artifacts Created
1. **GBIF record artifact** — full JSON record from GBIF
2. **Full paper artifact** — direct link via DOI resolver. Summary indicates whether paper is open access (full text available) or paywalled (abstract only).

## Note
Returns 404 if UUID is not found. Get UUIDs from `find_literature` search results — each result has an `id` field.
