import json
from agentsville.llm import client
from agentsville.prompts import ACTIVITY_AND_WEATHER_ARE_COMPATIBLE_SYSTEM_PROMPT


def check_weather_compatibility(activity: dict, weather: str) -> str:
    """
    Uses an LLM to determine whether an activity is compatible with the given weather.
    Returns exactly: "IS_COMPATIBLE" or "IS_INCOMPATIBLE".
    """

    user_input = f"""
            Activity: {json.dumps(activity)}
            Weather: "{weather}"
        """

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "system",
                "content": ACTIVITY_AND_WEATHER_ARE_COMPATIBLE_SYSTEM_PROMPT,
            },
            {"role": "user", "content": user_input},
        ],
    )

    text = response.output_text.strip()

    if text.startswith("IS_COMPATIBLE"):
        return "IS_COMPATIBLE"
    if text.startswith("IS_INCOMPATIBLE"):
        return "IS_INCOMPATIBLE"

    return "IS_INCOMPATIBLE"
