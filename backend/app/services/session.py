"""Interview lifecycle: ask a question, take an answer, finish and evaluate."""
from sqlalchemy.orm import Session

from .. import models
from ..config import settings
from . import evaluator, interviewer, memory


def get_turns(db: Session, interview_id: int) -> list[models.Turn]:
    return (
        db.query(models.Turn)
        .filter(models.Turn.interview_id == interview_id)
        .order_by(models.Turn.index)
        .all()
    )


def ask_next(db: Session, interview: models.Interview) -> models.Turn | None:
    turns = get_turns(db, interview.id)
    if len(turns) >= settings.max_questions:
        return None
    q = interviewer.next_question(interview, turns, memory.get_memory(db, interview.user_id))
    turn = models.Turn(
        interview_id=interview.id,
        index=len(turns),
        question=q["question"],
        topic=q["topic"],
        difficulty=q["difficulty"],
        kind=q["kind"],
    )
    db.add(turn)
    db.commit()
    db.refresh(turn)
    return turn


def submit_answer(
    db: Session, interview: models.Interview, text: str, code: str | None
) -> tuple[models.Turn, models.Turn | None]:
    if interview.status != "active":
        raise ValueError("Interview is not active")
    open_turn = next((t for t in reversed(get_turns(db, interview.id)) if t.answer is None), None)
    if open_turn is None:
        raise ValueError("There is no open question")
    open_turn.answer = text
    open_turn.code = code
    open_turn.evaluation = evaluator.evaluate_answer(interview, open_turn)
    db.commit()
    return open_turn, ask_next(db, interview)


def finalize(db: Session, interview_id: int) -> None:
    """Build the report and update the candidate's skill memory (runs in a Celery worker)."""
    interview = db.get(models.Interview, interview_id)
    if interview is None or interview.status == "completed":
        return
    answered = [t for t in get_turns(db, interview_id) if t.answer and t.evaluation]
    report = evaluator.build_report(interview, answered)
    interview.report = report
    interview.overall_score = report["overall_score"]
    interview.status = "completed"
    interview.finished_at = models.utcnow()
    memory.record_skill_scores(db, interview, report["skill_scores"])
    db.commit()
