"""Scores each answer on five criteria and builds the final report."""
import json
import logging
from collections import defaultdict

from .llm import llm

log = logging.getLogger(__name__)

CRITERIA = ["technical_accuracy", "communication", "reasoning", "completeness", "problem_solving"]

ANSWER_SYSTEM = """You are a strict but fair technical interviewer scoring one answer.
Score each criterion from 0 to 10: technical_accuracy, communication, reasoning, completeness, problem_solving.
If code is provided, judge correctness and approach too. Return JSON:
{"technical_accuracy": n, "communication": n, "reasoning": n, "completeness": n, "problem_solving": n,
 "feedback": "2-3 sentences: what was good, what was missing"}"""

REPORT_SYSTEM = """You write the end-of-interview report for a candidate. Be specific and constructive.
Return JSON: {"summary": "3-4 sentences", "strengths": [str], "weaknesses": [str],
"next_steps": [str, 3 concrete practice actions], "skill_notes": {"<skill>": "one-sentence note"}}"""


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _heuristic_scores(turn) -> dict:
    words = len((turn.answer or "").split())
    base = min(8.0, 3.0 + words / 12)
    if turn.code and len(turn.code.strip()) > 30:
        base = min(9.0, base + 1)
    return {c: round(base, 1) for c in CRITERIA} | {
        "feedback": "Offline mock evaluation based on answer length. Add an ANTHROPIC_API_KEY for real feedback."
    }


def evaluate_answer(interview, turn) -> dict:
    scores = None
    if llm.enabled:
        try:
            payload = {
                "role": interview.role,
                "level": interview.level,
                "question": turn.question,
                "difficulty": turn.difficulty,
                "answer": turn.answer,
                "code": turn.code,
            }
            scores = llm.complete_json(ANSWER_SYSTEM, json.dumps(payload))
        except Exception:
            log.exception("LLM evaluation failed; using heuristic")
    if scores is None:
        scores = _heuristic_scores(turn)

    clean = {c: max(0.0, min(10.0, float(scores.get(c, 0)))) for c in CRITERIA}
    clean["overall"] = round(_mean(list(clean.values())), 1)
    clean["feedback"] = str(scores.get("feedback", ""))
    return clean


def build_report(interview, turns: list) -> dict:
    by_skill: dict[str, list[float]] = defaultdict(list)
    for t in turns:
        by_skill[t.topic.strip().lower()].append(t.evaluation["overall"])
    skill_scores = {s: {"score": round(_mean(v), 1), "note": ""} for s, v in by_skill.items()}
    overall = round(_mean([t.evaluation["overall"] for t in turns]), 1) if turns else 0.0

    strengths = [s for s, v in skill_scores.items() if v["score"] >= 7]
    weaknesses = [s for s, v in skill_scores.items() if v["score"] < 6]
    narrative = {
        "summary": (
            f"You scored {overall}/10 across {len(turns)} questions for a {interview.level} "
            f"{interview.role} interview."
            if turns
            else "No questions were answered, so there is nothing to evaluate yet."
        ),
        "strengths": strengths,
        "weaknesses": weaknesses,
        "next_steps": [f"Practice {w}." for w in weaknesses[:3]],
    }

    if llm.enabled and turns:
        try:
            payload = {
                "role": interview.role,
                "level": interview.level,
                "overall_score": overall,
                "skill_scores": {s: v["score"] for s, v in skill_scores.items()},
                "turns": [
                    {"question": t.question, "topic": t.topic, "answer": t.answer,
                     "score": t.evaluation["overall"], "feedback": t.evaluation["feedback"]}
                    for t in turns
                ],
            }
            data = llm.complete_json(REPORT_SYSTEM, json.dumps(payload), max_tokens=1500)
            for key in ("summary", "strengths", "weaknesses", "next_steps"):
                if key in data:
                    narrative[key] = data[key]
            for skill, note in (data.get("skill_notes") or {}).items():
                if skill.lower() in skill_scores:
                    skill_scores[skill.lower()]["note"] = str(note)
        except Exception:
            log.exception("LLM report failed; using computed report")

    return {"overall_score": overall, "skill_scores": skill_scores, **narrative}
