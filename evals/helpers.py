import pathlib
import yaml


def load_tests(test_file: pathlib.Path):
    """loading test cases"""
    return yaml.safe_load(test_file.read_text())["test_cases"]


def parse_params(param_str: str) -> dict:
    """ parsing key value pairs into dict"""
    return dict(pair.split(": ") for pair in param_str.split(", "))


def normalize(value):
    """ converting to string for comparing """
    if value is None:
        return None
    if isinstance(value, list):
        return str(value[0]) if len(value) == 1 else ",".join(map(str, value))
    return str(value.value if hasattr(value, 'value') else value)
