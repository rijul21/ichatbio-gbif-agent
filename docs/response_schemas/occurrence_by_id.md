# Response Schema: find_occurrence_by_id
**Tool:** find_occurrence_by_id
**Endpoint:** `GET /v1/occurrence/{gbifId}`
**GBIF Service:** Occurrence Detail

---

## Response
Single occurrence record — same fields as `find_occurrence_records` but for one specific record.

## Key Fields
| Field | Type | Notes |
|-------|------|-------|
| gbifID | string | GBIF unique identifier — same as the ID used to fetch this record |
| scientificName | string | Matched scientific name |
| decimalLatitude / decimalLongitude | float | Coordinates if available |
| country | string | ISO 2-letter country code |
| stateProvince | string | State or province |
| eventDate | string | Date of observation |
| basisOfRecord | string | How record was created |
| recordedBy | string | Observer or collector |
| datasetName | string | Source dataset |
| issues | array | Data quality flags |
| media | array | Images or other media attached to record |

---

## Note
Returns 404 if the gbifID is not found. This entrypoint is for looking up a specific known record — not for searching. Use `find_occurrence_records` for searching by filters.
