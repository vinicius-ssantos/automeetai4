import pytest

def pytest_addoption(parser):
    parser.addoption(
        "--manual", action="store_true", default=False, help="run tests that call real APIs and consume credits"
    )

def pytest_configure(config):
    config.addinivalue_line("markers", "manual: marks tests that call real APIs and consume credits")

def pytest_collection_modifyitems(config, items):
    if not config.getoption("--manual"):
        skip_manual = pytest.mark.skip(reason="need --manual option to run tests that call real APIs")
        for item in items:
            if "manual" in item.keywords:
                item.add_marker(skip_manual)