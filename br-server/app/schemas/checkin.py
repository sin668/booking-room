from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class CheckinCalendarMark(BaseModel):
    date: date
    signed: bool = False
    missed: bool = False
    makeup_eligible: bool = False

    model_config = ConfigDict(from_attributes=True)


class CheckinSummaryResponse(BaseModel):
    today: date
    today_signed: bool
    streak: int
    total_days: int
    points: int
    makeup_cards: int
    calendar_mark: list[CheckinCalendarMark]
    missed_dates: list[date]

    model_config = ConfigDict(from_attributes=True)


class MakeupRequest(BaseModel):
    dates: list[date] = Field(..., min_length=1, max_length=30)


class CheckinActionResponse(BaseModel):
    summary: CheckinSummaryResponse
    reward_points: int = 0
    reward_cards: int = 0
    restored_dates: list[date] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
