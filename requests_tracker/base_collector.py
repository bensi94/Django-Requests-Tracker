import abc


class Collector(metaclass=abc.ABCMeta):
    """Base collector for all collectors except for MainRequestCollector"""

    @abc.abstractmethod
    def generate_statistics(self) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def matches_search_filter(self, search: str) -> bool:
        raise NotImplementedError()
