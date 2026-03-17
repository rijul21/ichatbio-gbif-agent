import sys
sys.path.append(".")

from src.models.validators import OccurrenceSearchParamsValidator

def run_test(name, params, user_request, should_pass):
    try:
        OccurrenceSearchParamsValidator.model_validate(
            params,
            context={"user_request": user_request}
        )
        result = "PASS"
        passed = True
    except Exception as e:
        result = f"FAIL - {str(e)[:80]}"
        passed = False

    expected = "PASS" if should_pass else "FAIL"
    status = "OK"
    if should_pass and not passed:
        status = "FALSE NEGATIVE - validator rejected correct extraction"
    elif not should_pass and passed:
        status = "VULNERABILITY - validator missed hallucinated value"

    print(f"\n{'='*60}")
    print(f"Test     : {name}")
    print(f"Request  : '{user_request}'")
    print(f"Params   : {params}")
    print(f"Expected : {expected} | Got: {'PASS' if passed else 'FAIL'}")
    print(f"Status   : {status}")


run_test(
    name="Hallucinated country",
    params={"country": "US", "scientificName": ["Aves"]},
    user_request="Find birds in North America",
    should_pass=False
)

run_test(
    name="Hallucinated year",
    params={"year": "2020", "scientificName": ["Aves"]},
    user_request="Find recent bird observations",
    should_pass=False
)

run_test(
    name="Hallucinated continent",
    params={"continent": "EUROPE", "scientificName": ["Puma concolor"]},
    user_request="Find records of Puma concolor",
    should_pass=False
)

run_test(
    name="Synonym mismatch - United States vs US",
    params={"taxonKey": 212, "country": "US"},
    user_request="Find birds in United States",
    should_pass=True
)

run_test(
    name="Synonym mismatch - North America vs NORTH_AMERICA",
    params={"continent": "NORTH_AMERICA", "scientificName": ["Aves"]},
    user_request="Find birds in North America",
    should_pass=True
)

# VULNERABILITY — hallucinated basis of record
run_test(
    name="Hallucinated basisOfRecord",
    params={"basisOfRecord": "HUMAN_OBSERVATION", "scientificName": ["Aves"]},
    user_request="Find bird records",
    should_pass=False
)

# VULNERABILITY — hallucinated state province
run_test(
    name="Hallucinated stateProvince",
    params={"stateProvince": "Florida", "scientificName": ["Aves"]},
    user_request="Find bird records in the US",
    should_pass=False
)

# FALSE NEGATIVE — correct year extraction
run_test(
    name="Correct year extraction",
    params={"year": "2020", "scientificName": ["Aves"]},
    user_request="Find bird records from 2020",
    should_pass=True
)

# FALSE NEGATIVE — scientific name correctly extracted from common name
run_test(
    name="Scientific name from common name",
    params={"scientificName": ["Aves"]},
    user_request="Find records of birds",
    should_pass=True
)

# FALSE NEGATIVE — country code from full name
run_test(
    name="Country code from full country name",
    params={"country": "BR", "scientificName": ["Panthera onca"]},
    user_request="Find jaguar records in Brazil",
    should_pass=True
)

# FALSE NEGATIVE — enum value with underscore
run_test(
    name="Enum underscore mismatch",
    params={"basisOfRecord": "PRESERVED_SPECIMEN", "scientificName": ["Aves"]},
    user_request="Find bird museum specimens",
    should_pass=True
)