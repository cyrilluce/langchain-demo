"""
Test script to demonstrate agent tool integration capability.
This shows how easy it will be to add tools to the agent in the future.
"""

import asyncio
from langchain.tools import tool
from app.agent import agent


@tool
def get_current_time() -> str:
    """Get the current time."""
    from datetime import datetime

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool
def calculate(expression: str) -> str:
    """
    Calculate a mathematical expression.

    Args:
        expression: A mathematical expression like "2 + 2" or "10 * 5"
    """
    try:
        result = eval(expression)
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {str(e)}"


async def test_without_tools() -> None:
    """Test agent without tools (current state)."""
    print("=== Testing Agent WITHOUT Tools ===")
    response = await agent.ainvoke("What is 25 * 4?")
    print(f"Response: {response}\n")


async def test_with_tools() -> None:
    """Test agent with tools (future capability)."""
    print("=== Testing Agent WITH Tools ===")

    # Add tools to the agent
    agent.add_tool(calculate)
    agent.add_tool(get_current_time)

    print(f"Tools added: {len(agent.tools)}")
    print(f"Tool names: {[getattr(t, 'name', str(t)) for t in agent.tools]}\n")

    # Test calculation tool
    response = await agent.ainvoke("What is 25 * 4? Use the calculator tool.")
    print(f"Calculation response: {response}\n")

    # Test time tool
    response = await agent.ainvoke("What is the current time?")
    print(f"Time response: {response}\n")


async def main() -> None:
    """Run tests."""
    try:
        await test_without_tools()
        print("\n" + "=" * 60 + "\n")
        await test_with_tools()
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
