from unittest.mock import MagicMock

import pytest

from cubeplex.sandbox.manager import SandboxManager


@pytest.fixture(autouse=True)
def _sandbox_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """Give manager-only tests the required OpenSandbox startup settings."""
    from cubeplex.config import config

    original_get = config.get
    required_values = {
        "sandbox.domain": "opensandbox.example:8090",
        "sandbox.image": "registry.example/cubeplex-sandbox:latest",
        "sandbox.api_key": "test-key",
    }

    def get(key: str, default: object = None, **kwargs: object) -> object:
        if key.startswith("sandbox."):
            return required_values.get(key, default)
        return original_get(key, default, **kwargs)

    monkeypatch.setattr(config, "get", get)


def test_build_user_volume_uses_stable_non_colliding_name(mock_encryption_backend):
    manager = SandboxManager(MagicMock(), mock_encryption_backend)

    first = manager._build_user_volume("ws-A", "user", "019d85a5-5bb7-7130-a4d2-a73734fa2dc6")
    second = manager._build_user_volume("ws-A", "user", "019d85a5-be69-76e2-b8cb-814a9440e4b0")
    repeated = manager._build_user_volume("ws-A", "user", "019d85a5-5bb7-7130-a4d2-a73734fa2dc6")
    other_ws = manager._build_user_volume("ws-B", "user", "019d85a5-5bb7-7130-a4d2-a73734fa2dc6")

    assert first.pvc is not None
    assert second.pvc is not None
    assert repeated.pvc is not None
    assert other_ws.pvc is not None
    assert first.pvc.claim_name == repeated.pvc.claim_name
    assert first.pvc.claim_name != second.pvc.claim_name
    # Same user in a different workspace gets a distinct PVC — the ownership
    # boundary the partial unique index enforces in the DB.
    assert first.pvc.claim_name != other_ws.pvc.claim_name
    assert first.pvc.claim_name.startswith("cubeplex-user-")


def test_create_timeout_overrides_request_timeout_for_create_only(mock_encryption_backend):
    manager = SandboxManager(MagicMock(), mock_encryption_backend)

    default = manager._build_connection_config()
    create = manager._build_connection_config(request_timeout=manager._create_timeout)

    # Ordinary commands use request_timeout (must cover max execute 1800s).
    # Create still passes create_timeout so a cold image pull has its own budget.
    assert default.request_timeout.total_seconds() == manager._request_timeout
    assert create.request_timeout.total_seconds() == manager._create_timeout
    assert manager._request_timeout >= 1800
    assert manager._create_timeout != manager._request_timeout
