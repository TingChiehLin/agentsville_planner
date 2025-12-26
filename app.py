from agentsville.planner import generate_itinerary
from agentsville.models import VacationInfo, Traveler
from agentsville.data_loader import load_activities, load_weather


def main():
    vacation = VacationInfo(
        destination="AgentsVille",
        start_date="2025-07-15",
        end_date="2025-07-18",
        interests=["food", "nature"],
        budget_usd=1000,
        travelers=[Traveler(name="Alice", age=30), Traveler(name="Bob", age=32)],
    )

    activities_data = load_activities()
    weather_data = load_weather()

    plan = generate_itinerary(
        vacation_info=vacation,
        activities_by_date=activities_data,
        weather_by_date=weather_data,
    )

    print(plan.total_cost_usd)
    print(plan.days[0].summary)


if __name__ == "__main__":
    main()
