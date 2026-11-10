from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = ""


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    full_name: str


class InterviewCreate(BaseModel):
    role: str = Field(min_length=2, max_length=80)
    level: Literal["junior", "mid", "senior"] = "mid"
    interview_type: Literal["technical", "coding", "behavioral", "system_design", "mixed"] = "mixed"
    focus: str = Field(default="", max_length=300)


class TurnOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    index: int
    question: str
    topic: str
    difficulty: int
    kind: str
    answer: str | None = None
    code: str | None = None
    evaluation: dict | None = None


class InterviewSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    role: str
    level: str
    interview_type: str
    focus: str
    status: str
    overall_score: float | None
    created_at: datetime


class InterviewOut(InterviewSummary):
    report: dict | None = None
    finished_at: datetime | None = None
    turns: list[TurnOut] = []


class AnswerIn(BaseModel):
    text: str = Field(min_length=1, max_length=8000)
    code: str | None = Field(default=None, max_length=20000)


class AnswerOut(BaseModel):
    evaluation: dict
    next: TurnOut | None


class CodeRunIn(BaseModel):
    code: str = Field(max_length=20000)
    language: Literal["python"] = "python"


class CodeRunOut(BaseModel):
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool


class SkillOut(BaseModel):
    skill: str
    latest: float
    previous_avg: float | None
    trend: float | None
    attempts: int
    history: list[float]


class ProfileOut(BaseModel):
    interviews_completed: int
    average_score: float | None
    skills: list[SkillOut]
    insights: list[str]
