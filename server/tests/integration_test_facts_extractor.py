"""
Integration test example for Facts Extractor API endpoint.

This is a manual test file showing how to test the API endpoint.
To run this test, ensure the server is running with DASHSCOPE_API_KEY set.

Usage:
    # Start the server
    ./dev.sh

    # In another terminal
    uv run python tests/integration_test_facts_extractor.py
"""

import asyncio
import httpx


async def test_facts_extraction():
    """Test the facts extraction endpoint."""
    base_url = "http://localhost:8000"

    # Test data
    test_request = {
        "content": """2024年全国机场信息汇总如下：
机场名称 | 客流吞吐量 | 货运量
武汉天河机场 | 3000万 | 50万吨
湖北花湖机场 | 500万 | 10万吨
宜昌三峡机场 | 200万 | 5万吨""",
        "topic": "湖北机场吞吐量"
    }

    async with httpx.AsyncClient() as client:
        # Check health first
        health_response = await client.get(f"{base_url}/health")
        print(f"Health check: {health_response.json()}")

        if not health_response.json().get("llm_configured"):
            print("⚠️  LLM not configured. Set DASHSCOPE_API_KEY to test.")
            return

        # Test facts extraction
        print("\n📝 Testing facts extraction...")
        print(f"Topic: {test_request['topic']}")
        print(f"Content length: {len(test_request['content'])} chars\n")

        response = await client.post(
            f"{base_url}/facts/extract",
            json=test_request,
            timeout=30.0
        )

        if response.status_code == 200:
            result = response.json()
            facts = result.get("facts", [])
            print(f"✅ Extracted {len(facts)} facts:\n")

            for i, fact_data in enumerate(facts, 1):
                fact = fact_data["fact"]
                references = fact_data["references"]

                print(f"{i}. {fact}")
                print(f"   References ({len(references)}):")

                for ref in references:
                    offset = ref["offset"]
                    length = ref["length"]
                    text = test_request["content"][offset:offset + length]
                    print(f"   - Position {offset}, Length {length}")
                    print(f"     Text: \"{text}\"")
                print()

        elif response.status_code == 503:
            print(f"❌ LLM service error: {response.json()}")
        else:
            print(f"❌ Error {response.status_code}: {response.text}")


async def test_edge_cases():
    """Test edge cases."""
    base_url = "http://localhost:8000"

    test_cases = [
        {
            "name": "Empty content",
            "request": {"content": "", "topic": "test"},
            "expected_status": 422  # Validation error
        },
        {
            "name": "Empty topic",
            "request": {"content": "some content", "topic": ""},
            "expected_status": 422  # Validation error
        },
    ]

    async with httpx.AsyncClient() as client:
        print("\n🧪 Testing edge cases...\n")

        for test_case in test_cases:
            print(f"Testing: {test_case['name']}")
            response = await client.post(
                f"{base_url}/facts/extract",
                json=test_case["request"],
                timeout=10.0
            )

            if response.status_code == test_case["expected_status"]:
                print(f"✅ Passed (status {response.status_code})")
            else:
                print(
                    f"❌ Failed: expected {test_case['expected_status']}, "
                    f"got {response.status_code}"
                )
            print()


async def main():
    """Run all integration tests."""
    try:
        await test_facts_extraction()
        await test_edge_cases()
        print("✨ Integration tests completed!")
    except httpx.ConnectError:
        print("❌ Cannot connect to server. Is it running?")
        print("   Run './dev.sh' to start the server.")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
