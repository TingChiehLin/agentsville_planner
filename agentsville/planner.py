import json
from typing import Dict, List

from agentsville.prompts import ITINERARY_AGENT_SYSTEM_PROMPT
from agentsville.models import VacationInfo, TravelPlan
from agentsville.llm import client


def build_user_prompt(
    vacation_info: VacationInfo,
    activities_by_date: Dict[str, List[dict]],
    weather_by_date: Dict[str, str],
) -> str:
    result = f"""
        VacationInfo:
    {vacation_info.model_dump_json(indent=2)}

    Activities:
    {json.dumps(activities_by_date, indent=2)}

    Weather:
    {json.dumps(weather_by_date, indent=2)}
    """.strip()
    return result


def generate_itinerary(
    vacation_info: VacationInfo,
    activities_by_date: Dict[str, List[dict]],
    weather_by_date: Dict[str, str],
) -> TravelPlan:
    """
    Calls the LLM itinerary agent and returns a validated TravelPlan.
    """

    user_prompt = build_user_prompt(
        vacation_info,
        activities_by_date,
        weather_by_date,
    )

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": ITINERARY_AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )

    # Extract raw text output
    raw_output = response.output_text.strip()

    # Validate + parse JSON into Pydantic model
    try:
        travel_plan = TravelPlan.model_validate_json(raw_output)
    except Exception as e:
        raise ValueError(
            f"LLM output is not valid TravelPlan JSON.\n\nOutput:\n{raw_output}"
        ) from e

    return travel_plan
