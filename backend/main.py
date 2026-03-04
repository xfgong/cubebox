"""
Entry point for cubebox Backend.

Starts the FastAPI application with uvicorn.
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "cubebox.api.app:create_app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        factory=True,
    )
