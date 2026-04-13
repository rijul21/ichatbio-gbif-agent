import pathlib
import pytest
from evals.helpers import load_tests
from evals.checks import check_params, check_portal_url, check_description, check_reply

TEST_FILE = pathlib.Path(__file__).parent / "test_sets" / "count_species_records.yaml"
test_cases = load_tests(TEST_FILE)


@pytest.mark.asyncio
@pytest.mark.parametrize("test_case", test_cases)
async def test_count_species_records(run_agent, test_case):
    result = await run_agent("count_species_records", test_case["user_message"])
    
    # Check if this is an expected rejection (location-based query)
    if test_case.get("expect_rejection"):
        assert "location" in result["reply"].lower() or "occurrence" in result["reply"].lower(), \
            f"Expected rejection for location query, got: {result['reply']}"
        return
    
    if param := test_case.get("expected_param"):
        check_params(result["params"], param)
        check_portal_url(result["portal_url"], param)
    
    assert result["description"], "No description returned"
    check_description(result["description"], test_case["expected_description"])
    
    if expected_reply := test_case.get("expected_reply"):
        assert result["reply"], "No reply returned"
        check_reply(result["reply"], expected_reply)
