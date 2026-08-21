from abc import ABC, abstractmethod
from typing import AsyncGenerator, Callable, List, Optional
from swaram.core.events import (
    CandleEvent,
    FundingEvent,
    MarkSpotPriceEvent,
    OrderbookEvent,
    TickEvent,
    TradeEvent,
)


class BaseMarketDataProvider(ABC):
    """Abstract interface for all Swaram market data providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier name (e.g. 'delta', 'bybit', 'ctrader')."""
        pass

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection with the remote data source."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Gracefully disconnect and cleanup resources."""
        pass

    @abstractmethod
    async def subscribe(self, symbols: List[str], channels: Optional[List[str]] = None) -> None:
        """Subscribe to specific symbols and channels."""
        pass

    @abstractmethod
    async def stream_events(self) -> AsyncGenerator[object, None]:
        """Yield normalized domain events as they arrive."""
        pass
