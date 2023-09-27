import pytest

from figurative.utils import log


@pytest.fixture(scope="session", autouse=True)
def initialize_figurative_logging(request):
    """Initialize Figurative's logger for all tests"""
    log.init_logging()
