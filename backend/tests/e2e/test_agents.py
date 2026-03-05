"""E2E tests for streaming API endpoint

Tests the POST /api/v1/agents/run endpoint with real API calls
using test environment configuration.
"""

from fastapi.testclient import TestClient

from tests.e2e.helpers import assert_event_contains, parse_sse_events


class TestAPIEventStream:
    """Event stream format and structure tests"""

    def test_api_event_stream_complete(self, client: TestClient) -> None:
        """Test event stream has correct structure and order

        Validates: Requirements 4.2, 7.3
        """
        response = client.post(
            "/api/v1/agents/run",
            json={"input": "Calculate 2 + 3"},
        )

        assert response.status_code == 200
        events = parse_sse_events(response.text)

        # Verify stream has events
        assert len(events) >= 3

        # Verify event types
        event_types = [event.type for event in events]
        assert "chain_start" in event_types
        assert "done" in event_types

        # Verify no error events in successful execution
        assert "error" not in event_types, (
            f"Unexpected error event in successful execution: {events}"
        )

        # Verify order: chain_start first, done last
        assert events[0].type == "chain_start"
        assert events[-1].type == "done"

        # Verify all events have timestamps
        for event in events:
            assert event.timestamp is not None
            assert len(event.timestamp) > 0

        # Verify chain_start has input
        chain_start = events[0]
        assert_event_contains(chain_start, ["input"])
        assert chain_start.data["input"] == "Calculate 2 + 3"


class TestAPIErrorHandling:
    """Error handling and validation tests"""

    def test_api_empty_input(self, client: TestClient) -> None:
        """Test empty input returns 400 error

        Validates: Requirements 4.3, 5.1, 5.2
        """
        response = client.post(
            "/api/v1/agents/run",
            json={"input": ""},
        )

        assert response.status_code == 400

    def test_api_missing_input_field(self, client: TestClient) -> None:
        """Test missing input field returns 422 error

        Validates: Requirements 4.3, 5.1, 5.2
        """
        response = client.post(
            "/api/v1/agents/run",
            json={},
        )

        assert response.status_code == 422

    def test_api_invalid_json(self, client: TestClient) -> None:
        """Test invalid JSON returns 422 error

        Validates: Requirements 4.3, 5.1, 5.2
        """
        response = client.post(
            "/api/v1/agents/run",
            content="invalid json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422
