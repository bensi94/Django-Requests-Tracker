import django
import pytest
from django.test import RequestFactory


def pytest_sessionstart() -> None:
    django.setup()


@pytest.fixture
def request_factory() -> RequestFactory:
    return RequestFactory()
