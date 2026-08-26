import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.llm.client import chat

def test_llm():
    """Test basic LLM functionality"""
    print("Testing LLM connection...")

    messages = [
        {"role": "user", "content": "Say hello in one short sentence."}
    ]

    try:
        response = chat(messages)
        content = response.choices[0].message.content
        print(f"\n✓ LLM Response: {content}\n")
        return True
    except Exception as e:
        print(f"\n✗ LLM Error: {e}\n")
        return False

def test_agent_conversation():
    """Test multi-turn conversation with agent"""
    print("Testing agent conversation flow...")

    conversation = [
        {"role": "system", "content": "You are a helpful dental clinic assistant. Keep responses brief."},
        {"role": "user", "content": "Hi, I need a teeth cleaning appointment"}
    ]

    try:
        # First turn
        response = chat(conversation)
        assistant_msg = response.choices[0].message.content
        print(f"\nUser: Hi, I need a teeth cleaning appointment")
        print(f"Assistant: {assistant_msg}")

        # Add to conversation
        conversation.append({"role": "assistant", "content": assistant_msg})
        conversation.append({"role": "user", "content": "What are your available times?"})

        # Second turn
        response = chat(conversation)
        assistant_msg = response.choices[0].message.content
        print(f"\nUser: What are your available times?")
        print(f"Assistant: {assistant_msg}\n")

        return True
    except Exception as e:
        print(f"\n✗ Conversation Error: {e}\n")
        return False

def test_tool_calling():
    """Test LLM with tool calling"""
    print("Testing tool calling capability...")

    tools = [
        {
            "type": "function",
            "function": {
                "name": "check_availability",
                "description": "Check available appointment slots",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                        "service": {"type": "string", "description": "Service type"}
                    },
                    "required": ["date"]
                }
            }
        }
    ]

    messages = [
        {"role": "system", "content": "You are a dental clinic assistant with access to booking tools."},
        {"role": "user", "content": "Can you check availability for tomorrow for a cleaning?"}
    ]

    try:
        response = chat(messages, tools=tools, tool_choice="auto")
        message = response.choices[0].message

        print(f"\nUser: Can you check availability for tomorrow for a cleaning?")

        if message.tool_calls:
            tool_call = message.tool_calls[0]
            print(f"✓ Tool Called: {tool_call.function.name}")
            print(f"  Arguments: {tool_call.function.arguments}\n")
            return True
        else:
            print(f"Assistant: {message.content}")
            print("⚠ No tool call made (some models may not support tools)\n")
            return True
    except Exception as e:
        print(f"\n✗ Tool Calling Error: {e}\n")
        return False

def main():
    print("=" * 60)
    print("FOLLOWLY AGENT CLI TEST")
    print("=" * 60)
    print()

    # Check environment
    provider = os.getenv("LLM_PROVIDER", "openrouter")
    print(f"LLM Provider: {provider}")

    if provider == "openrouter":
        key = os.getenv("OPENROUTER_API_KEY")
        model = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")
    elif provider == "openai":
        key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    elif provider == "anthropic":
        key = os.getenv("ANTHROPIC_API_KEY")
        model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
    else:
        print(f"Unknown provider: {provider}")
        return

    print(f"Model: {model}")

    if not key:
        print(f"\n✗ API key not set! Please set {provider.upper()}_API_KEY in .env\n")
        return

    print()
    print("-" * 60)

    # Run tests
    results = []

    results.append(("Basic LLM Test", test_llm()))
    results.append(("Conversation Test", test_agent_conversation()))
    results.append(("Tool Calling Test", test_tool_calling()))

    # Summary
    print("-" * 60)
    print("SUMMARY")
    print("-" * 60)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\nPassed: {passed}/{total}")
    print()

if __name__ == "__main__":
    main()
