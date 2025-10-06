"""Main terminal loop for the calendar assistant. Handles user input, interpretation, and calendar actions."""

from dotenv import load_dotenv

# Load .env.local first for local dev overrides, then .env
try:
    load_dotenv(".env.local", override=True)
except Exception:
    pass
load_dotenv()

import openai_client
from utils.command_dispatcher import dispatch
from utils.cli_output import render
from core.conversation_manager import ConversationState

# Main terminal loop
if __name__ == "__main__":
    print("Welcome to the Terminal Calendar Assistant! Type 'exit' to quit.")

    # Initialize conversation state for session memory
    conversation_state = ConversationState()
    turn_count = 0

    while True:
        user_input = input("\n> ")
        if user_input.lower() in ["exit", "quit", "q"]:
            print("Goodbye!")
            break

        # Build conversation context for LLM, including current user input on subsequent turns
        if conversation_state.turn_count > 0:
            # Include recent turns and the current user input in context
            context = conversation_state.get_context_for_llm_prompt()
            context += f"\nUser: {user_input}"
        else:
            # No context on first turn
            context = ""

        # Interpret the command using GPT-4o with conversation context
        interpreted = openai_client.interpret_command(user_input, context)
        print(f"\n[Interpreted]: {interpreted}")

        # Handle different action types
        action = interpreted.get("action") if interpreted else None
        details = interpreted.get("details") if interpreted else {}
        if not isinstance(details, dict):
            details = {}

        start_date = details.get("start_date")
        end_date = details.get("end_date")

        # Dispatch action to handler
        try:
            result = dispatch(action, details)
        except KeyError:
            print("[Not implemented yet]")
            result = {"error": "not_implemented"}

        # Print structured result for CLI/API-first workflows
        try:
            payload = {
                "type": action or "unknown",
                "result": result if isinstance(result, dict) else details,
            }
            print(render(payload))
        except Exception:
            # Fallback to previous behavior if rendering fails
            pass

        # Update conversation state with this turn
        conversation_state.append_turn(user_input, action, details)
        turn_count += 1
