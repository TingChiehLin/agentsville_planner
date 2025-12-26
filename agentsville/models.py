from pydantic import BaseModel
from typing import List, Optional
from datetime import date


class Traveler(BaseModel):
    name: str
    age: Optional[int] = None


class VacationInfo(BaseModel):
    destination: str
    start_date: date
    end_date: date
    interests: List[str]
    budget_usd: float
    travelers: List[Traveler]


class Activity(BaseModel):
    id: str
    name: str
    description: str
    duration_hours: float
    cost_usd: float
    suitability: List[str]
    weather_suitable: List[str]


class DayPlan(BaseModel):
    date: date
    summary: str
    activities: List[Activity]
    estimated_cost_usd: float


class TravelPlan(BaseModel):
    destination: str
    start_date: date
    end_date: date
    total_cost_usd: float
    days: List[DayPlan]
    notes: Optional[str] = None
