"""Interview Memory & Candidate Intelligence: skill history across all of a user's interviews."""
from collections import defaultdict

from sqlalchemy.orm import Session

from .. import models

WEAK_BELOW = 6.0
IMPROVED_BY = 1.0


def record_skill_scores(db: Session, interview: models.Interview, skill_scores: dict) -> None:
    for skill, info in skill_scores.items():
        db.add(
            models.SkillScore(
                user_id=interview.user_id,
                interview_id=interview.id,
                skill=skill,
                score=info["score"],
                note=info.get("note", ""),
            )
        )


def skill_history(db: Session, user_id: int) -> dict[str, list[float]]:
    rows = (
        db.query(models.SkillScore)
        .filter(models.SkillScore.user_id == user_id)
        .order_by(models.SkillScore.created_at, models.SkillScore.id)
        .all()
    )
    history: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        history[row.skill].append(row.score)
    return history


def summarize(history: dict[str, list[float]]) -> list[dict]:
    skills = []
    for skill, scores in history.items():
        latest, earlier = scores[-1], scores[:-1]
        previous_avg = round(sum(earlier) / len(earlier), 1) if earlier else None
        trend = round(latest - previous_avg, 1) if previous_avg is not None else None
        skills.append(
            {"skill": skill, "latest": latest, "previous_avg": previous_avg,
             "trend": trend, "attempts": len(scores), "history": scores}
        )
    return sorted(skills, key=lambda s: s["latest"])


def make_insights(skills: list[dict]) -> list[str]:
    improved = [s for s in skills if s["trend"] is not None and s["trend"] >= IMPROVED_BY]
    weak = [s for s in skills if s["latest"] < WEAK_BELOW]
    regressed = [s for s in skills if s["trend"] is not None and s["trend"] <= -IMPROVED_BY]
    insights = [f"You have improved in {s['skill']} (+{s['trend']} vs your earlier average)." for s in improved]
    insights += [f"{s['skill'].capitalize()} dropped ({s['trend']}); worth a refresher." for s in regressed]
    insights += [f"{s['skill'].capitalize()} remains an area to practice (latest {s['latest']}/10)." for s in weak]
    return insights


def get_memory(db: Session, user_id: int) -> dict:
    """Compact memory handed to the interviewer so questions target known gaps."""
    skills = summarize(skill_history(db, user_id))
    return {
        "weak": [s["skill"] for s in skills if s["latest"] < WEAK_BELOW][:5],
        "improved": [s["skill"] for s in skills if s["trend"] is not None and s["trend"] >= IMPROVED_BY][:5],
    }


def build_profile(db: Session, user_id: int) -> dict:
    skills = summarize(skill_history(db, user_id))
    done = (
        db.query(models.Interview)
        .filter(models.Interview.user_id == user_id, models.Interview.status == "completed")
        .all()
    )
    scores = [i.overall_score for i in done if i.overall_score is not None]
    return {
        "interviews_completed": len(done),
        "average_score": round(sum(scores) / len(scores), 1) if scores else None,
        "skills": skills,
        "insights": make_insights(skills),
    }
