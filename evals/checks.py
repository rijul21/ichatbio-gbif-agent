import pytest
from urllib.parse import urlparse, parse_qs
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from src.log import logger
from evals.helpers import parse_params, normalize


# metrics for GEval
description_metric = GEval(
    name="Description Equivalence",
    criteria="Are the descriptions semantically equivalent? Same organism, location, time. Cosmetic differences okay.",
    evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
    model="gpt-4.1-mini"
)

reply_metric = GEval(
    name="Reply Quality",
    criteria="Does the reply correctly summarize what was done? Check: 1) Confirms action completed, 2) Mentions relevant details (record count or ID), 3) Includes portal URL. Minor wording differences okay.",
    evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
    model="gpt-4.1-mini"
)


def check_params(actual: dict, expected_str: str):
    """Check params match, fail on mismatch"""
    expected = parse_params(expected_str)
    errors = [
        f"{k}: expected {v}, got {normalize(actual.get(k))}"
        for k, v in expected.items()
        if normalize(actual.get(k)) != v
    ]
    if errors:
        logger.info(f"Param Check FAILED | {errors}")
        pytest.fail(f"Param mismatch: {'; '.join(errors)}")
    logger.info(f"Param Check PASSED | {list(expected.keys())}")


def check_portal_url(url: str, expected_str: str):
    """Check portal URL contains expected params"""
    if not url:
        return
    
    parsed = urlparse(url)
    if parsed.netloc != "gbif.org":
        pytest.fail(f"Wrong domain: {parsed.netloc}")
    
    url_params = parse_qs(parsed.query)
    expected = parse_params(expected_str)
    
    missing = [k for k in expected if k not in url_params and k not in ['limit', 'offset', 'shuffle']]
    if missing:
        logger.info(f"Portal URL missing params: {missing}")
    else:
        logger.info(f"Portal URL Check PASSED")


def check_description(actual: str, expected: str):
    """Check description using GEval"""
    case = LLMTestCase(input="", expected_output=expected, actual_output=actual)
    description_metric.measure(case)
    logger.info(f"Description | actual={actual} | expected={expected} | score={description_metric.score:.2f}")
    assert description_metric.score >= 0.5, f"Description failed: {description_metric.reason}"


def check_reply(actual: str, expected: str):
    """Check reply using GEval"""
    case = LLMTestCase(input="", expected_output=expected, actual_output=actual)
    reply_metric.measure(case)
    logger.info(f"Reply | score={reply_metric.score:.2f} | reason={reply_metric.reason}")
    assert reply_metric.score >= 0.5, f"Reply failed: {reply_metric.reason}"
