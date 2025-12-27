import json
from typing import List
from agentsville.weather import check_weather_compatibility


def get_activities_by_date_tool(date_str: str, activities_db: dict) -> str:
    """
    get_activities_by_date_tool(date_str: str, activities_db: dict) -> str
    Returns JSON string: {"date": "...", "activities": [ ... ]}

    date_str: "YYYY-MM-DD"
    activities_db: dictionary mapping date->list(activity dicts)
    """
    activities = activities_db.get(date_str, [])
    return json.dumps({"date": date_str, "activities": activities})


def calculator_tool(expression: str) -> str:
    """
    calculator_tool(expression: str) -> str
    returns: {"expression": "...", "result": numeric}
    """
    import numexpr as ne

    res = float(ne.evaluate(expression))
    return json.dumps({"expression": expression, "result": res})


def run_evals_tool(itinerary_json: str, weather_json: str, activities_db: dict) -> str:
    """
    Evaluates itinerary constraints and flags issues.
    Weather compatibility is evaluated via LLM.
    """

    plan = json.loads(itinerary_json)
    weather = json.loads(weather_json)

    issues = []

    for day in plan.get("days", []):
        date = day.get("date")

        # Minimum activities per day
        if len(day.get("activities", [])) < 2:
            issues.append({"date": date, "issue": "fewer than 2 activities"})

        day_weather = weather.get(date)

        if not day_weather:
            continue

        for act in day.get("activities", []):
            result = check_weather_compatibility(act, day_weather)

            if result == "IS_INCOMPATIBLE":
                issues.append(
                    {
                        "date": date,
                        "activity": act.get("name"),
                        "issue": f"incompatible with {day_weather}",
                    }
                )

    passed = len(issues) == 0

    return json.dumps(
        {"passed": passed, "issues": issues, "summary": f"{len(issues)} issue(s)"}
    )


def final_answer_tool(final_travelplan_json: str) -> str:
    """
    final_answer_tool(final_travelplan_json:str) -> str
    Returns acknowledgement string. Used to finish ReAct loop.
    """
    return "FINAL_OK"
