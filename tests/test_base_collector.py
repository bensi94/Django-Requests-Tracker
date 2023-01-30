import pytest

from requests_tracker.base_collector import Collector


class FakeCollector(Collector):
    def generate_statistics(self) -> None:
        return super().generate_statistics()

    def matches_search_filter(self, search: str) -> bool:
        return super().matches_search_filter(search)  # type: ignore


def test_generate_statistics() -> None:

    collector = FakeCollector()

    with pytest.raises(NotImplementedError):
        collector.generate_statistics()


def test_matches_search_filter() -> None:

    collector = FakeCollector()

    with pytest.raises(NotImplementedError):
        collector.matches_search_filter("fake")
