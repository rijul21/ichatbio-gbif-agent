import pathlib

import pytest
import yaml
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams


#constants 

CRITICAL_KEYS = {
    "count":  {"country", "taxonKey"},
    "search": {"country", "taxonKey", "classKey", "stateProvince", "year", "basisOfRecord", "continent", "eventDate"},
}

equivalence = GEval(
    name="Equivalence",
    criteria="Determine if the 'actual output' is semantically equivalent to 'expected output'. Cosmetic differences are okay.",
    evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
    model="gpt-4.1-mini"
)

#helpers

def load_tests(filename):
    file = pathlib.Path(__file__).parent / "test_sets" / filename
    with open(file) as f:
        return yaml.safe_load(f)["test_cases"]


def critical_params(params: dict, keys: set) -> str:
    return str({k: v for k, v in params.items() if k in keys})


def eval_and_assert(label: str, actual: str, expected: str):
    case = LLMTestCase(input="", expected_output=expected, actual_output=actual)
    equivalence.measure(case)
    print(f"\n  {label}")
    print(f"  actual   : {actual}")
    print(f"  expected : {expected}")
    print(f"  score    : {equivalence.score:.2f}")
    print(f"  reason   : {equivalence.reason}")
    assert equivalence.score >= 0.5, f"{label} failed: {equivalence.reason}"


# test data 

by_id_tests    = load_tests("find_occurrence_by_id.yaml")
count_tests    = load_tests("count_occurrence_records.yaml")
find_tests     = load_tests("find_occurrence_records.yaml")

#tests 

@pytest.mark.asyncio
@pytest.mark.parametrize("user_message,expected_param", [(t["user_message"], t["expected_param"]) for t in by_id_tests])
async def test_find_occurrence_by_id(run_agent, user_message, expected_param):
    result = await run_agent("find_occurrence_by_id", user_message)
    eval_and_assert("params", str(result["params"]), expected_param)


@pytest.mark.asyncio
@pytest.mark.parametrize("user_message,expected_param", [(t["user_message"], t["expected_param"]) for t in count_tests])
async def test_count_occurrence_records(run_agent, user_message, expected_param):
    result = await run_agent("count_occurrence_records", user_message)
    eval_and_assert("params", critical_params(result["params"], CRITICAL_KEYS["count"]), expected_param)


@pytest.mark.asyncio
@pytest.mark.parametrize("user_message,expected_param", [(t["user_message"], t["expected_param"]) for t in find_tests])
async def test_find_occurrence_records(run_agent, user_message, expected_param):
    result = await run_agent("find_occurrence_records", user_message)
    eval_and_assert("params", critical_params(result["params"], CRITICAL_KEYS["search"]), expected_param)