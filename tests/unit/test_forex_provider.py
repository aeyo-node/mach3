import pytest
from swaram.core.events import TickEvent
from swaram.providers.forex.ctrader import CTraderForexProvider


@pytest.fixture
def provider():
    return CTraderForexProvider()


def test_provider_name(provider):
    assert provider.name == "ctrader"


@pytest.mark.asyncio
async def test_stream_events(provider):
    provider._running = True
    event_gen = provider.stream_events()
    event = await anext(event_gen)
    provider._running = False
    
    assert isinstance(event, TickEvent)
    assert event.provider == "ctrader"
    assert event.bid is not None
    assert event.ask is not None
    assert event.bid < event.ask
