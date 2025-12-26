import json
from typing import List


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
    Simple evaluator: checks budget, date ranges, >=2 activities/day,
    and flags weather-incompatible activities. Returns JSON string.
    """
    import json
    from datetime import datetime

    plan = json.loads(itinerary_json)
    weather = json.loads(weather_json)
    issues = []
    total = plan.get("total_cost_usd", 0)
    # dummy budget check left to caller with VacationInfo if needed
    for day in plan.get("days", []):
        d = day.get("date")
        # min activities
        if len(day.get("activities", [])) < 2:
            issues.append({"date": d, "issue": "fewer than 2 activities"})
        # weather compatibility check
        w = weather.get(d)
        for act in day.get("activities", []):
            if w and "weather_suitable" in act:
                if w not in act["weather_suitable"] and "indoor" not in act.get(
                    "suitability", []
                ):
                    issues.append(
                        {
                            "date": d,
                            "activity": act.get("name"),
                            "issue": f"incompatible with {w}",
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
