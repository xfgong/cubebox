"""LLM Factory Usage Example

Demonstrates how to use the LLM factory with config.yaml configuration.
"""

import asyncio

from cubebox.llm.factory import LLMFactory


async def main():
    """Example usage of LLM factory"""

    # Initialize factory (loads from config.yaml)
    factory = LLMFactory()

    # List available providers
    print("Available providers:")
    for provider in factory.list_providers():
        print(f"  - {provider}")
        models = factory.list_models(provider)
        print(f"    Models: {', '.join(models)}")

    print("\n" + "=" * 60 + "\n")

    # Example 1: Create LLM with provider_name and model_id
    print("Example 1: Create LLM with provider_name and model_id")
    llm = factory.create(
        model_id="doubao-seed-1.8",
        provider_name="sensedeal-ai",
        temperature=0.7,
    )
    print(f"Created LLM: {llm}")

    # Test the LLM
    print("\nTesting LLM with a simple question...")
    response = await llm.ainvoke("What is 2+2? Answer briefly.")
    print(f"Response: {response.content}")

    # Check for reasoning content (if available)
    reasoning = response.additional_kwargs.get("reasoning_content")
    if reasoning:
        print(f"Reasoning: {reasoning}")

    print("\n" + "=" * 60 + "\n")

    # Example 2: Create LLM with only model_id (auto-find provider)
    print("Example 2: Create LLM with only model_id (auto-find provider)")
    llm_qwen = factory.create(
        model_id="qwen3-max-2026-01-23",
        temperature=0.5,
        max_tokens=1000,  # Override model's default
    )
    print(f"Created Qwen LLM: {llm_qwen}")

    response_qwen = await llm_qwen.ainvoke("Explain Python in one sentence.")
    print(f"Qwen Response: {response_qwen.content}")

    print("\n" + "=" * 60 + "\n")

    # Example 3: Get model configuration
    print("Example 3: Get model configuration")
    model_config = factory.get_model_config("sensedeal-ai", "doubao-seed-1.8")
    print(f"Model: {model_config.name}")
    print(f"Context Window: {model_config.context_window}")
    print(f"Max Tokens: {model_config.max_tokens}")
    print(f"Reasoning: {model_config.reasoning}")
    print(f"Input Cost: ${model_config.cost.input}/M tokens")
    print(f"Output Cost: ${model_config.cost.output}/M tokens")


if __name__ == "__main__":
    asyncio.run(main())
