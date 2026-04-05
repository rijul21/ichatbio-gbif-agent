import pathlib
import pytest
from evals.helpers import load_tests
from evals.checks import check_params, check_description, check_reply

TEST_FILE = pathlib.Path(__file__).parent / "test_sets" / "find_occurrence_by_id.yaml"
test_cases = load_tests(TEST_FILE)


@pytest.mark.asyncio
@pytest.mark.parametrize("test_case", test_cases)
async def test_find_occurrence_by_id(run_agent, test_case):
    result = await run_agent("find_occurrence_by_id", test_case["user_message"])
    
    if param := test_case.get("expected_param"):
        check_params(result["params"], param)
    
    assert result["description"], "No description returned"
    check_description(result["description"], test_case["expected_description"], by_id=True)
    
    if expected_reply := test_case.get("expected_reply"):
        assert result["reply"], "No reply returned"
        check_reply(result["reply"], expected_reply)
