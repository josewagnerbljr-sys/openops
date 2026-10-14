import pytest

from openops_core.events import EventBus, EventHandlingError


def test_publish_calls_subscribed_handlers():
    bus = EventBus()
    received = []

    bus.subscribe("sop.completed", lambda event: received.append(event.payload))

    bus.publish("sop.completed", {"sop_id": "SOP-RESTAURANT-001"})

    assert received == [{"sop_id": "SOP-RESTAURANT-001"}]


def test_publish_with_no_subscribers_does_not_raise():
    bus = EventBus()

    event = bus.publish("nobody.listening")

    assert event.name == "nobody.listening"


def test_unsubscribe_stops_further_notifications():
    bus = EventBus()
    calls = []
    handler = lambda event: calls.append(event)

    bus.subscribe("stock.low", handler)
    bus.unsubscribe("stock.low", handler)
    bus.publish("stock.low")

    assert calls == []


def test_one_failing_handler_does_not_block_others():
    bus = EventBus()
    calls = []

    def failing_handler(event):
        raise RuntimeError("boom")

    def working_handler(event):
        calls.append(event.name)

    bus.subscribe("risky.event", failing_handler)
    bus.subscribe("risky.event", working_handler)

    with pytest.raises(EventHandlingError) as exc_info:
        bus.publish("risky.event")

    assert calls == ["risky.event"]
    assert len(exc_info.value.errors) == 1


def test_subscriber_count():
    bus = EventBus()
    bus.subscribe("x", lambda e: None)
    bus.subscribe("x", lambda e: None)

    assert bus.subscriber_count("x") == 2
    assert bus.subscriber_count("y") == 0
