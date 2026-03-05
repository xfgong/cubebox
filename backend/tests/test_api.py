"""E2E tests for streaming API endpoint

Tests the POST /api/v1/agents/run endpoint with real API calls
using test environment configuration.
"""

import os

import pytest
from fastapi.testclient import TestClient

from cubebox.api.app import create_app
from tests.conftest import assert_event_contains, parse_sse_events


@pytest.fixture(scope="session", autouse=True)
def setup_test_env() -> None:
    """Set up test environment configuration

    Ensures test config is loaded before any tests run
    """
    os.environ["ENV_FOR_DYNACONF"] = "test"


@pytest.fixture
def client() -> TestClient:
    """Create test client for API testing with test config

    Returns:
        TestClient instance
    """
    app = create_app()
    return TestClient(app)


class TestAPIBasic:
    """Basic API functionality tests"""

    def test_api_valid_request(self, client: TestClient) -> None:
        """Test valid request returns 200 with SSE stream

        Validates: Requirements 4.1, 4.2
        """
        response = client.post(
            "/api/v1/agents/run",
            json={"input": "What is 2 + 3?"},
        )

        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        assert len(response.text) > 0
        assert "data: " in response.text


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
