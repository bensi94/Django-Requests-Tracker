import django


def pytest_sessionstart() -> None:
    django.setup()
