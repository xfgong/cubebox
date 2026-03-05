"""Example: Using LLM with Reasoning Content Support

This example demonstrates how to use the LLM factory with OpenAI-compatible
endpoints that support reasoning content in their responses.
"""

import asyncio

from cubebox.llm import ChatOpenAICompatible, LLMConfig, LLMFactory


def example_with_factory():
    """Example using LLMFactory for OpenAI-compatible endpoint with reasoning model."""
    print("=== Example 1: Using LLMFactory with Reasoning Model ===\n")

    # Create LLM config for OpenAI-compatible endpoint with reasoning model
    config = LLMConfig(
        provider="openai",
        model="doubao-seed-1.6-lite-thinking",
        api_key="sd-moltbot-NDjKH1Kh4BElYUa4OXP4Mia0NZc3oBU",
        base_url="https://gateway.chat.sensedeal.vip/v1",
        temperature=0.7,
    )

    # Factory will automatically use ChatOpenAICompatible for custom base_url
    llm = LLMFactory.create(config)

    # Invoke the model with a reasoning task
    response = llm.invoke("What is 3 to the power of 3? Think step by step.")

    # Print response
    print(f"Answer: {response.content}\n")

    # Check for reasoning content
    reasoning = response.additional_kwargs.get("reasoning_content")
    if reasoning:
        print(f"Reasoning Process:\n{reasoning}\n")
    else:
        print("No reasoning_content field in response\n")

    # Check for reasoning tokens (alternative way to detect reasoning)
    token_usage = response.response_metadata.get("token_usage", {})
    completion_details = token_usage.get("completion_tokens_details", {})
    reasoning_tokens = completion_details.get("reasoning_tokens", 0)

    if reasoning_tokens > 0:
        print(f"✓ Model used reasoning: {reasoning_tokens} reasoning tokens")
        print(f"  Total tokens: {token_usage.get('total_tokens', 0)}")
        print(f"  Completion tokens: {token_usage.get('completion_tokens', 0)}\n")
    else:
        print("No reasoning tokens detected\n")


def example_direct_usage():
    """Example using ChatOpenAICompatible directly with reasoning model."""
    print("=== Example 2: Direct Usage with Reasoning Model ===\n")

    # Create model directly with reasoning model
    llm = ChatOpenAICompatible(
        model="doubao-seed-1.6-lite-thinking",
        base_url="https://gateway.chat.sensedeal.vip/v1",
        api_key="sd-moltbot-NDjKH1Kh4BElYUa4OXP4Mia0NZc3oBU",
        temperature=0.7,
    )

    # Invoke with a reasoning task
    response = llm.invoke(
        "Solve this problem: If a train travels 120 km in 2 hours, "
        "what is its average speed? Show your reasoning."
    )

    print(f"Answer: {response.content}\n")

    # Access reasoning if available
    reasoning = response.additional_kwargs.get("reasoning_content")
    if reasoning:
        print(f"Reasoning Process:\n{reasoning}\n")
    else:
        print("No reasoning_content field in response\n")

    # Show reasoning token usage
    token_usage = response.response_metadata.get("token_usage", {})
    completion_details = token_usage.get("completion_tokens_details", {})
    reasoning_tokens = completion_details.get("reasoning_tokens", 0)

    if reasoning_tokens > 0:
        print(f"✓ Reasoning tokens used: {reasoning_tokens}")
        print("  (The model performed internal reasoning, but content not exposed)\n")


def example_streaming():
    """Example with streaming responses from reasoning model."""
    print("=== Example 3: Streaming with Reasoning Model ===\n")

    llm = ChatOpenAICompatible(
        model="doubao-seed-1.6-lite-thinking",
        base_url="https://gateway.chat.sensedeal.vip/v1",
        api_key="sd-moltbot-NDjKH1Kh4BElYUa4OXP4Mia0NZc3oBU",
        temperature=0.7,
    )

    print("Streaming response:")
    reasoning_parts = []
    content_parts = []

    # Use synchronous stream
    for chunk in llm.stream("Calculate 15 * 8 and explain your steps."):
        # Collect content
        if chunk.content:
            content_parts.append(chunk.content)
            print(chunk.content, end="", flush=True)

        # Check for reasoning in chunks
        if chunk.additional_kwargs.get("reasoning_content"):
            reasoning_parts.append(chunk.additional_kwargs["reasoning_content"])

    print("\n")

    # Print collected reasoning if any
    if reasoning_parts:
        print(f"Reasoning Process (streamed):\n{''.join(reasoning_parts)}\n")
        print(f"Total reasoning chunks: {len(reasoning_parts)}\n")
    else:
        print("No reasoning content in stream\n")


def example_official_openai_reasoning():
    """Example using official OpenAI API with Responses API for reasoning."""
    print("=== Example 4: Official OpenAI with Reasoning ===\n")

    # For official OpenAI reasoning models (o1, o3, etc.)
    config = LLMConfig(
        provider="openai",
        model="o1-mini",  # or "o3-mini", "gpt-5-nano", etc.
        api_key="your-openai-api-key",  # Replace with actual key
        reasoning={
            "effort": "medium",  # 'low', 'medium', 'high'
            "summary": "auto",  # 'detailed', 'auto', or None
        },
    )

    # Factory will use ChatOpenAI with Responses API
    _ = LLMFactory.create(config)

    # Note: This requires a valid OpenAI API key
    # response = llm.invoke("What is 3^3?")
    # for block in response.content_blocks:
    #     if block["type"] == "reasoning":
    #         print(f"Reasoning: {block['summary']}")

    print("(Requires valid OpenAI API key - example code shown above)\n")


async def example_async_invoke():
    """Example using async invoke with reasoning model."""
    print("=== Example 5: Async Invoke with Reasoning Model ===\n")

    llm = ChatOpenAICompatible(
        model="doubao-seed-1.6-lite-thinking",
        base_url="https://gateway.chat.sensedeal.vip/v1",
        api_key="sd-moltbot-NDjKH1Kh4BElYUa4OXP4Mia0NZc3oBU",
        temperature=0.7,
    )

    # Async invoke
    response = await llm.ainvoke("Calculate the factorial of 5. Show your reasoning step by step.")

    print(f"Answer: {response.content}\n")

    # Access reasoning if available
    reasoning = response.additional_kwargs.get("reasoning_content")
    if reasoning:
        print(f"Reasoning Process:\n{reasoning}\n")
    else:
        print("No reasoning_content field in response\n")

    # Show token usage
    token_usage = response.response_metadata.get("token_usage", {})
    if token_usage:
        print(f"Token usage: {token_usage}\n")


async def example_async_streaming():
    """Example with async streaming responses from reasoning model."""
    print("=== Example 6: Async Streaming with Reasoning Model ===\n")

    llm = ChatOpenAICompatible(
        model="doubao-seed-1.6-lite-thinking",
        base_url="https://gateway.chat.sensedeal.vip/v1",
        api_key="sd-moltbot-NDjKH1Kh4BElYUa4OXP4Mia0NZc3oBU",
        temperature=0.7,
    )

    print("Streaming response (async):")
    reasoning_parts = []
    content_parts = []

    # Use async stream
    async for chunk in llm.astream(
        "What is the sum of all numbers from 1 to 100? Explain your approach."
    ):
        # Collect content
        if chunk.content:
            content_parts.append(chunk.content)
            print(chunk.content, end="", flush=True)

        # Check for reasoning in chunks
        if chunk.additional_kwargs.get("reasoning_content"):
            reasoning_parts.append(chunk.additional_kwargs["reasoning_content"])

    print("\n")

    # Print collected reasoning if any
    if reasoning_parts:
        print(f"Reasoning Process (streamed):\n{''.join(reasoning_parts)}\n")
        print(f"Total reasoning chunks: {len(reasoning_parts)}\n")
    else:
        print("No reasoning content in stream\n")


if __name__ == "__main__":
    # Run sync examples
    example_with_factory()
    example_direct_usage()
    example_streaming()
    example_official_openai_reasoning()

    # Run async examples
    print("\n=== Running Async Examples ===\n")
    asyncio.run(example_async_invoke())
    asyncio.run(example_async_streaming())

    print("=== All examples completed ===")
