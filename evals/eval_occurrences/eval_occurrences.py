import pathlib
import pytest
import yaml
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams


def load_tests(filename):
    file = pathlib.Path(__file__).parent / "test_sets" / filename
    with open(file) as f:
        return yaml.safe_load(f)["test_cases"]


description_equivalence = GEval(
    name="Description Equivalence",
    criteria="Determine if the actual description is semantically equivalent to the expected description. "
             "They should describe the same organism, location, and time period. Cosmetic differences are okay.",
    evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
    model="gpt-4.1-mini"
)

by_id_equivalence = GEval(
    name="By ID Description Equivalence",
    criteria="Determine if the actual description correctly describes an occurrence record lookup. "
             "It should mention the occurrence ID or record details. Cosmetic differences are okay.",
    evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
    model="gpt-4.1-mini"
)


def eval_description(actual: str, expected: str, metric=description_equivalence):
    case = LLMTestCase(input="", expected_output=expected, actual_output=actual)
    metric.measure(case)
    print(f"\n  Description Check:")
    print(f"    actual   : {actual}")
    print(f"    expected : {expected}")
    print(f"    score    : {metric.score:.2f}")
    print(f"    reason   : {metric.reason}")
    assert metric.score >= 0.5, f"Description check failed: {metric.reason}"


find_tests = load_tests("find_occurrence_records.yaml")
find_by_id_tests = load_tests("find_occurrence_by_id.yaml")
count_tests = load_tests("count_occurrence_records.yaml")


@pytest.mark.asyncio
@pytest.mark.parametrize("test_case", find_tests)
async def test_find_occurrence_records(run_agent, test_case):
    user_message = test_case["user_message"]
    expected_description = test_case["expected_description"]

    result = await run_agent("find_occurrence_records", user_message)

    if "description" not in result:
        pytest.fail("No artifact returned - agent likely asked for clarification")

    eval_description(result["description"], expected_description)


@pytest.mark.asyncio
@pytest.mark.parametrize("test_case", find_by_id_tests)
async def test_find_occurrence_by_id(run_agent, test_case):
    user_message = test_case["user_message"]
    expected_description = test_case["expected_description"]

    result = await run_agent("find_occurrence_by_id", user_message)

    if "description" not in result:
        pytest.fail("No artifact returned - agent likely asked for clarification")

    eval_description(result["description"], expected_description, metric=by_id_equivalence)


@pytest.mark.asyncio
@pytest.mark.parametrize("test_case", count_tests)
async def test_count_occurrence_records(run_agent, test_case):
    user_message = test_case["user_message"]
    expected_description = test_case["expected_description"]

    result = await run_agent("count_occurrence_records", user_message)

    if "description" not in result:
        pytest.fail("No artifact returned - agent likely asked for clarification")

    eval_description(result["description"], expected_description)