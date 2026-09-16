"""
Core agent loop.

Flow per the architecture diagram:
  build messages -> call Groq w/ tools -> tool call? ->
    yes -> execute tool -> feed result back -> loop
    no  -> return final text

Two guardrails baked in:
  1. MAX_TOOL_ITERATIONS caps how many tool round-trips one turn can take,
     so a confused/looping LLM can't spin forever.
  2. escalate_to_human is intercepted specially: the moment the LLM calls
     it, we stop trusting the LLM's own text for this turn entirely and
     return the fixed ESCALATION_MESSAGE instead. This is what makes the
     "drop a canned message" guardrail solid — the reply the customer sees
     is hardcoded Python, not anything the LLM generated.
"""

import json

from groq import Groq

from app.config import GROQ_API_KEY, GROQ_MODEL
from app.agent.prompts import build_system_prompt
from app.agent.tools import TOOL_SCHEMAS, TOOL_FUNCTIONS
from app.agent.tools.escalate import ESCALATION_MESSAGE

client = Groq(api_key=GROQ_API_KEY)

MAX_TOOL_ITERATIONS = 5


def run_agent_turn(phone_number: str, user_message: str, history: list[dict] | None = None) -> tuple[str, list[dict]]:
    """
    Run one full turn of the agent loop for a single customer message.

    Args:
        phone_number: customer's WhatsApp number.
        user_message: the new message text from the customer.
        history: prior messages in Groq's format (list of role/content dicts),
                 or None to start a fresh conversation.

    Returns:
        (reply_text, updated_history) — updated_history should be persisted
        (later, via app/agent/state.py) so the next turn has context.
    """
    messages = list(history) if history else [{"role": "system", "content": build_system_prompt()}]
    messages.append({"role": "user", "content": user_message})

    for _ in range(MAX_TOOL_ITERATIONS):
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
        )

        message = response.choices[0].message

        # No tool call -> plain text reply, we're done.
        if not message.tool_calls:
            messages.append({"role": "assistant", "content": message.content})
            return message.content, messages

        # Append the assistant's tool-call message before handling calls,
        # as Groq/OpenAI-style APIs require it in the running history.
        messages.append(
            {
                "role": "assistant",
                "content": message.content,
                "tool_calls": [tc.model_dump() for tc in message.tool_calls],
            }
        )

        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name

            # --- Escalation short-circuit ---
            if tool_name == "escalate_to_human":
                try:
                    args = json.loads(tool_call.function.arguments)
                except (json.JSONDecodeError, TypeError):
                    args = {"phone_number": phone_number, "reason": "unparseable escalation call"}
                TOOL_FUNCTIONS["escalate_to_human"](**args)
                # Stop entirely — do not let the LLM produce further text this turn.
                return ESCALATION_MESSAGE, messages

            # --- Normal tool execution, defensive JSON parsing ---
            try:
                args = json.loads(tool_call.function.arguments)
            except (json.JSONDecodeError, TypeError):
                result = {"error": "Malformed tool arguments, could not parse."}
            else:
                func = TOOL_FUNCTIONS.get(tool_name)
                if func is None:
                    result = {"error": f"Unknown tool '{tool_name}'."}
                else:
                    try:
                        result = func(**args)
                    except Exception as e:
                        result = {"error": str(e)}

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": json.dumps(result),
                }
            )
        # loop continues -> next iteration sends tool results back to Groq

    # Safety net: too many tool round-trips without a final answer.
    fallback = "Sorry, I'm having trouble processing that right now — let me get a team member to help."
    messages.append({"role": "assistant", "content": fallback})
    return fallback, messages


if __name__ == "__main__":
    # Quick manual CLI test — run with: python -m app.agent.loop
    TEST_PHONE = "+923001234567"
    history = None
    print("Chat with the agent (type 'quit' to exit).\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == "quit":
            break
        reply, history = run_agent_turn(TEST_PHONE, user_input, history)
        print(f"Agent: {reply}\n")
