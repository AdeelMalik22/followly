import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.llm.client import chat

def interactive_chat():
    """Interactive chat session with the agent"""
    print("=" * 60)
    print("FOLLOWLY AGENT - INTERACTIVE CLI")
    print("=" * 60)
    print()

    provider = os.getenv("LLM_PROVIDER", "openrouter")
    print(f"Provider: {provider}")

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
        print(f"\n✗ API key not set! Set {provider.upper()}_API_KEY in .env\n")
        return

    print()
    print("Commands: /exit, /reset, /help")
    print("-" * 60)
    print()

    # Initialize conversation with system prompt
    conversation = [
        {
            "role": "system",
            "content": """You are an AI assistant for a dental clinic called "Bright Smiles Dental".

Your role:
- Answer questions about dental services
- Help patients book appointments
- Qualify leads by asking about their needs
- Be friendly, professional, and concise

Services offered:
- Regular Cleaning: $120, 45 minutes
- Teeth Whitening: $350, 60 minutes
- Dental Exam: $80, 30 minutes
- Cavity Filling: $200-400, 60 minutes
- Root Canal: $800-1200, 90 minutes

Office hours: Mon-Fri 9am-6pm, Sat 9am-2pm

Current date: 2026-08-26"""
        }
    ]

    while True:
        try:
            user_input = input("\n\033[94mYou:\033[0m ").strip()

            if not user_input:
                continue

            # Commands
            if user_input == "/exit":
                print("\nGoodbye!")
                break
            elif user_input == "/reset":
                conversation = conversation[:1]  # Keep system prompt
                print("\n✓ Conversation reset\n")
                continue
            elif user_input == "/help":
                print("\nCommands:")
                print("  /exit  - Exit the chat")
                print("  /reset - Reset conversation history")
                print("  /help  - Show this help\n")
                continue

            # Add user message
            conversation.append({"role": "user", "content": user_input})

            # Get response
            response = chat(conversation)
            assistant_msg = response.choices[0].message.content

            # Add assistant message
            conversation.append({"role": "assistant", "content": assistant_msg})

            # Display response
            print(f"\n\033[92mAssistant:\033[0m {assistant_msg}")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\n\033[91m✗ Error:\033[0m {e}")

if __name__ == "__main__":
    interactive_chat()
