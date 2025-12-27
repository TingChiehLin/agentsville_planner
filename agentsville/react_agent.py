import json
import re
from typing import Any, Dict, Optional

from agentsville.utils import make_json_safe

from agentsville.prompts import ITINERARY_REVISION_AGENT_SYSTEM_PROMPT
from agentsville.models import TravelPlan
from agentsville.llm import client
from agentsville.tools import (
    get_activities_by_date_tool,
    run_evals_tool,
    calculator_tool,
    final_answer_tool,
)


# Think -> Act -> feedback -> Observation
# Helpers: parse ACTION JSON robustly
def _find_json_substring(text: str) -> Optional[str]:
    """
    Find the first balanced JSON object starting at the first '{' after 'ACTION:'.
    Returns the JSON substring or None.
    """
    start = text.find("{", text.find("ACTION"))
    if start == -1:
        # fallback: find first '{' anywhere
        start = text.find("{")
        if start == -1:
            return None

    depth = 0
    for i in range(start, len(text)):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def parse_thought_and_action(response_text: str) -> Dict[str, Any]:
    """
    Parses a response containing THOUGHT: ... ACTION: {...}
    Returns {"thought": str, "action": dict}
    Raises ValueError if parsing fails.
    """
    # Normalize whitespace
    t = response_text.strip()

    # Extract THOUGHT (text between 'THOUGHT:' and 'ACTION:')
    thought_match = re.search(
        r"THOUGHT\s*:\s*(.*?)\s*ACTION\s*:", t, flags=re.IGNORECASE | re.DOTALL
    )
    if thought_match:
        thought = thought_match.group(1).strip()
    else:
        # Attempt fallback: take first line as thought
        thought = t.splitlines()[0].strip()

    # Extract JSON after ACTION:
    json_sub = _find_json_substring(t)
    if not json_sub:
        raise ValueError("Could not find ACTION JSON in LLM response.")

    try:
        action = json.loads(json_sub)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"ACTION JSON invalid: {e}; substring: {json_sub[:200]}"
        ) from e

    return {"thought": thought, "action": action}


def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    """
    Map tool_name to the actual tool function and execute it.
    Returns the tool's observation string (JSON string).
    """
    if tool_name == "get_activities_by_date_tool":
        # expected arguments: date_str, activities_db
        date_str = arguments.get("date_str")
        activities_db = arguments.get("activities_db")
        return get_activities_by_date_tool(date_str, activities_db)
    elif tool_name == "run_evals_tool":
        itinerary_json = arguments.get("itinerary_json")
        weather_json = arguments.get("weather_json")
        activities_db = arguments.get("activities_db")
        return run_evals_tool(itinerary_json, weather_json, activities_db)
    elif tool_name == "calculator_tool":
        expr = arguments.get("expression")
        return calculator_tool(expr)
    elif tool_name == "final_answer_tool":
        final_json = arguments.get("final_travelplan_json")
        return final_answer_tool(final_json)
    else:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})


# ReAct loop
def revise_itinerary_with_react_agent(
    initial_itinerary: Dict[str, Any],
    weather_data: Dict[str, Any],
    activities_db: Dict[str, Any],
    max_iterations: int = 15,
    model: str = "gpt-4.1-mini",
) -> TravelPlan:
    """
    Use a ReAct agent to iteratively revise the itinerary until run_evals_tool passes and final_answer_tool is called.
    initial_itinerary: dict (TravelPlan JSON-like)
    weather_data: dict
    activities_db: dict
    Returns: validated TravelPlan
    """

    safe_itinerary = make_json_safe(initial_itinerary)
    safe_weather = make_json_safe(weather_data)

    # conversation history for the Responses API input
    conversation = [
        {"role": "system", "content": ITINERARY_REVISION_AGENT_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Initial itinerary: {json.dumps(safe_itinerary)}",
        },
        {
            "role": "user",
            "content": f"Weather data: {json.dumps(safe_weather)}",
        },
    ]

    # Track whether run_evals_tool has been called and passed
    run_evals_called_and_passed = False

    for iteration in range(max_iterations):
        # Call the LLM
        response = client.responses.create(
            model=model,
            input=conversation,
            temperature=0.2,
        )
        # Prefer response.output_text if available
        resp_text = getattr(response, "output_text", None)
        if not resp_text:
            # Fallback: try to extract first text chunk
            try:
                resp_text = ""
                for out in response.output:
                    for item in out.get("content", []):
                        if item.get("type") == "output_text":
                            resp_text += item.get("text", "")
            except Exception:
                resp_text = str(response)

        # Parse thought and action
        try:
            parsed = parse_thought_and_action(resp_text)
        except ValueError as e:
            # If parsing fails, add observation and continue
            conversation.append({"role": "assistant", "content": resp_text})
            conversation.append(
                {
                    "role": "user",
                    "content": f"OBSERVATION: Could not parse ACTION JSON: {e}",
                }
            )
            continue

        thought = parsed["thought"]
        action = parsed["action"]

        # Append assistant message with THOUGHT+ACTION (so history records their reply)
        conversation.append(
            {
                "role": "assistant",
                "content": f"THOUGHT: {thought}\nACTION: {json.dumps(action)}",
            }
        )

        tool_name = action.get("tool_name")
        arguments = action.get("arguments", {})

        # Enforce that final_answer_tool cannot be called before run_evals_tool has passed
        if tool_name == "final_answer_tool" and not run_evals_called_and_passed:
            obs = json.dumps(
                {
                    "error": "final_answer_tool not allowed until run_evals_tool has been run and passed."
                }
            )
            conversation.append({"role": "user", "content": f"OBSERVATION: {obs}"})
            continue

        # Execute the tool
        try:
            observation = execute_tool(tool_name, arguments)
        except Exception as exc:
            observation = json.dumps({"error": f"Tool execution error: {exc}"})

        # Add observation to conversation
        conversation.append({"role": "user", "content": f"OBSERVATION: {observation}"})

        # If tool was run_evals_tool, inspect result and set flag
        if tool_name == "run_evals_tool":
            try:
                eval_result = json.loads(observation)

                if eval_result.get("passed") is True:
                    run_evals_called_and_passed = True

                    conversation.append(
                        {
                            "role": "user",
                            "content": (
                                "OBSERVATION: Evaluation PASSED. "
                                "You MUST now call final_answer_tool with the final TravelPlan JSON."
                            ),
                        }
                    )
                else:
                    run_evals_called_and_passed = False
            except Exception:
                run_evals_called_and_passed = False

        # If tool was final_answer_tool and run_evals_called_and_passed True, return final TravelPlan
        if tool_name == "final_answer_tool":
            # final_answer_tool's arguments should have included final_travelplan_json; validate it
            final_json_str = arguments.get("final_travelplan_json")
            if not final_json_str:
                raise RuntimeError(
                    "final_answer_tool called without final_travelplan_json argument."
                )
            # Validate with Pydantic
            try:
                plan = TravelPlan.model_validate_json(final_json_str)
                return plan
            except Exception as e:
                raise RuntimeError(f"Final TravelPlan invalid: {e}")

    # If loop ends without final, raise
    raise RuntimeError(
        "ReAct agent exceeded max iterations without returning a final plan."
    )
