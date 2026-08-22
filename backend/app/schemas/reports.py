from pydantic import BaseModel
from typing import List

class DashboardStats(BaseModel):
    total_events: int
    active_events: int
    total_registered_participants: int
    total_allocated_tickets: int

class DashboardStatsResponse(BaseModel):
    success: bool = True
    data: DashboardStats

class HourlyCheckIn(BaseModel):
    hour: str
    count: int

class EventStats(BaseModel):
    tickets_issued: int
    checked_in: int
    remaining: int
    attendance_percentage: float
    check_ins_over_time: List[HourlyCheckIn]

class EventStatsResponse(BaseModel):
    success: bool = True
    data: EventStats
