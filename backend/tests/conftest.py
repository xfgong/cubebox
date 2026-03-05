"""Pytest configuration and fixtures for E2E testing

Provides utilities for:
- SSE event parsing
- Event validation helpers
- Test configuration
"""

import json

from cubebox.agents.schemas import AgentEvent


def parse_sse_events(response_text: str) -> list[AgentEvent]:
    """Parse SSE formatted event stream

    Parses Server-Sent Events format: "data: {json}\n\n"

    Args:
        response_text: Raw SSE response text

    Returns:
        List of AgentEvent objects parsed from the stream

    Raises:
        ValueError: If event parsing fails
    """
    events: list[AgentEvent] = []

    # Split by double newline to get individual events
    event_strings = response_text.split("\n\n")

    for event_str in event_strings:
        event_str = event_str.strip()
        if not event_str:
            continue

        # Remove "data: " prefix
        if event_str.startswith("data: "):
            json_str = event_str[6:]  # Remove "data: " prefix
        else:
            continue

        try:
            event_data = json.loads(json_str)
            # Convert to AgentEvent
            event = AgentEvent(**event_data)
            events.append(event)
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Failed to parse SSE event: {event_str}") from e

    return events


def assert_event_type(event: AgentEvent, expected_type: str) -> None:
    """Verify event type matches expected value

    Args:
        event: AgentEvent to verify
        expected_type: Expected event type string

    Raises:
        AssertionError: If event type doesn't match
    """
    assert event.type == expected_type, f"Expected event type '{expected_type}', got '{event.type}'"


def assert_event_contains(
    event: AgentEvent,
    expected_keys: list[str],
) -> None:
    """Verify event data contains expected keys

    Args:
        event: AgentEvent to verify
        expected_keys: List of keys that should be in event.data

    Raises:
        AssertionError: If any expected key is missing
    """
    for key in expected_keys:
        assert key in event.data, (
            f"Expected key '{key}' in event data, got keys: {list(event.data.keys())}"
        )
