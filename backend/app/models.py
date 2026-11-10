from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120), default="")
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Interview(Base):
    __tablename__ = "interviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[str] = mapped_column(String(80))
    level: Mapped[str] = mapped_column(String(30))
    interview_type: Mapped[str] = mapped_column(String(30), default="mixed")
    focus: Mapped[str] = mapped_column(String(300), default="")  # company / technology / weak skills
    status: Mapped[str] = mapped_column(String(20), default="active")  # active | evaluating | completed
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    report: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    turns: Mapped[list["Turn"]] = relationship(
        back_populates="interview", order_by="Turn.index", cascade="all, delete-orphan"
    )


class Turn(Base):
    """One question/answer exchange, including its evaluation."""

    __tablename__ = "turns"

    id: Mapped[int] = mapped_column(primary_key=True)
    interview_id: Mapped[int] = mapped_column(ForeignKey("interviews.id"), index=True)
    index: Mapped[int] = mapped_column(Integer)
    question: Mapped[str] = mapped_column(Text)
    topic: Mapped[str] = mapped_column(String(60), default="general")
    difficulty: Mapped[int] = mapped_column(Integer, default=3)
    kind: Mapped[str] = mapped_column(String(20), default="conceptual")  # conceptual | coding | behavioral | system_design
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    code: Mapped[str | None] = mapped_column(Text, nullable=True)
    evaluation: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    interview: Mapped[Interview] = relationship(back_populates="turns")


class SkillScore(Base):
    """Interview memory: one row per (interview, skill). History powers the candidate profile."""

    __tablename__ = "skill_scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    interview_id: Mapped[int] = mapped_column(ForeignKey("interviews.id"), index=True)
    skill: Mapped[str] = mapped_column(String(60), index=True)
    score: Mapped[float] = mapped_column(Float)
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
