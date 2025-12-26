import json
from agentsville.models import TravelPlan


def test_travelplan_validates(sample_plan_json):
    plan = TravelPlan.model_validate_json(json.dumps(sample_plan_json))
    assert plan.total_cost_usd <= 10000
