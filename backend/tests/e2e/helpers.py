import json

from cubebox.agents.schemas import AgentEvent


def parse_sse_events(response_text: str) -> list[AgentEvent]:
    events: list[AgentEvent] = []
    for event_str in response_text.split("\n\n"):
        event_str = event_str.strip()
        if not event_str or not event_str.startswith("data: "):
            continue
        try:
            event = AgentEvent(**json.loads(event_str[6:]))
            events.append(event)
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Failed to parse SSE event: {event_str}") from e
    return events


def assert_event_contains(event: AgentEvent, expected_keys: list[str]) -> None:
    for key in expected_keys:
        assert key in event.data, (
            f"Expected key '{key}' in event data, got keys: {list(event.data.keys())}"
        )
