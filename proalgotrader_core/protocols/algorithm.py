"""Protocol for Algorithm."""

from abc import abstractmethod
from asyncio import Protocol

from proalgotrader_core.protocols.base_algorithm import BaseAlgorithmProtocol


class AlgorithmProtocol(BaseAlgorithmProtocol, Protocol):
    """Protocol for Algorithm functionality.

    Extends BaseAlgorithmProtocol with abstract methods that must be
    implemented by any trading algorithm.
    """

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the algorithm. Called once before run()."""
        ...

    @abstractmethod
    async def next(self) -> None:
        """Execute one iteration of the algorithm. Called in a loop."""
        ...
