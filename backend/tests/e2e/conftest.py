import pytest
from fastapi.testclient import TestClient

from cubebox.api.app import create_app


@pytest.fixture
def client() -> TestClient:
    """Create test client for API testing with test config

    Returns:
        TestClient instance
    """
    app = create_app()
    return TestClient(app)
