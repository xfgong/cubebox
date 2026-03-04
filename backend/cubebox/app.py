"""Application State Management

Stores application-level singleton objects such as client instances.
"""


class AppState:
    """Application state container"""

    def __init__(self):
        self.llm_client = None
        self.sandbox_client = None
        self.mcp_manager = None


# Global application state instance
app_state = AppState()
