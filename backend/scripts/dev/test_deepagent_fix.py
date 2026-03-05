"""Test script to verify DeepAgent integration fix"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cubebox.agents.executor import DeepAgentExecutor


async def main() -> None:
    """Test the DeepAgentExecutor with a simple query"""
    print("Initializing DeepAgentExecutor...")
    executor = DeepAgentExecutor()

    print("\nStreaming agent execution...")
    print("-" * 50)

    async for event in executor.stream("What is 2 + 3?"):
        print(f"Event: {event.type}")
        if hasattr(event, "data"):
            print(f"Data: {event.data}")
        print()

    print("-" * 50)
    print("Test completed!")


if __name__ == "__main__":
    asyncio.run(main())
