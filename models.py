from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class MilestoneStatus(str, Enum):
    pending = "pending"
    completed = "completed"
    overdue = "overdue"


class DriftLevel(str, Enum):
    on_track = "on_track"
    slight_drift = "slight_drift"
    major_drift = "major_drift"
    stalled = "stalled"


class FounderCreate(BaseModel):
    name: str = Field(max_length=100)
    github_username: str = Field(max_length=50)
    project_name: str = Field(max_length=100)
    goal: str = Field(max_length=500)


class MilestoneCreate(BaseModel):
    title: str = Field(max_length=200)
    due_date: str
    commit_target: int = Field(ge=1, default=5, description="Target number of commits by due date")


class FounderResponse(BaseModel):
    id: int
    name: str
    github_username: str
    project_name: str
    goal: str
    created_at: str
    drift_level: str = "on_track"
    total_commits: int = 0


class MilestoneResponse(BaseModel):
    id: int
    founder_id: int
    title: str
    due_date: str
    commit_target: int
    current_commits: int = 0
    status: str = "pending"
    created_at: str


class CheckinResponse(BaseModel):
    founder_id: int
    founder_name: str
    drift_level: str
    milestones_on_track: int
    milestones_overdue: int
    simulated_commits: int
    message: str
