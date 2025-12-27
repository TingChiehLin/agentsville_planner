from agentsville.planner import generate_itinerary
from agentsville.models import VacationInfo, Traveler
from agentsville.data_loader import load_activities, load_weather
from agentsville.react_agent import revise_itinerary_with_react_agent


def main():
    activities_data = load_activities()
    weather_data = load_weather()

    vacation = VacationInfo(
        destination="AgentsVille",
        start_date="2025-07-15",
        end_date="2025-07-18",
        interests=["food", "nature"],
        budget_usd=1000,
        travelers=[Traveler(name="Alice", age=30), Traveler(name="Bob", age=32)],
    )

    # initial itinerary
    initial_plan = generate_itinerary(
        vacation_info=vacation,
        activities_by_date=activities_data,
        weather_by_date=weather_data,
    )

    print(initial_plan.total_cost_usd)
    print(initial_plan.days[0].summary)

    # call ReAct agent with initial plan
    final_plan = revise_itinerary_with_react_agent(
        initial_itinerary=initial_plan.model_dump(),
        weather_data=weather_data,
        activities_db=activities_data,
        max_iterations=8,
    )

    print("Final plan summary:")
    print("Total cost:", final_plan.total_cost_usd)
    for d in final_plan.days:
        print(d.date, "-", d.summary)


if __name__ == "__main__":
    main()
