"""The adaptive interviewer: picks the next question from the transcript, difficulty and memory."""
import json
import logging

from .llm import llm

log = logging.getLogger(__name__)

BASE_DIFFICULTY = {"junior": 2, "mid": 3, "senior": 4}

SYSTEM = """You are a senior engineer conducting a realistic job interview.
Ask exactly ONE question at a time. React to the candidate's previous answer: if it was shallow or
partly wrong, probe deeper on that gap; if it was strong, move to a harder related topic or a practical
scenario. Never reveal answers or give feedback inside the question. Keep questions under 80 words.
Return JSON: {"question": str, "topic": str (1-3 word skill tag, lowercase), "difficulty": int 1-5, "kind": str}."""

FALLBACK_BANK = [
    ("Walk me through a project you're proud of and the hardest technical decision you made in it.", "experience", "behavioral"),
    ("What is the difference between synchronous and asynchronous programming?", "concurrency", "conceptual"),
    ("How would you design a REST API for a to-do app with users and shared lists?", "api design", "conceptual"),
    ("Explain database indexing. When can an index hurt performance?", "databases", "conceptual"),
    ("Write a function that returns the first non-repeating character in a string, and explain its complexity.", "algorithms", "coding"),
    ("An endpoint makes three independent HTTP requests. How would you run them concurrently and handle one failing?", "concurrency", "conceptual"),
    ("How would you find and fix a slow SQL query in production?", "query optimization", "conceptual"),
    ("Tell me about a time you disagreed with a teammate. How was it resolved?", "communication", "behavioral"),
]


def target_difficulty(level: str, turns: list) -> int:
    """Raise difficulty after strong answers, lower it after weak ones."""
    base = BASE_DIFFICULTY.get(level, 3)
    scored = [t for t in turns if t.evaluation]
    if not scored:
        return base
    recent = [t.evaluation["overall"] for t in scored[-2:]]
    avg = sum(recent) / len(recent)
    d = scored[-1].difficulty
    if avg >= 7.5:
        d += 1
    elif avg < 5:
        d -= 1
    return max(1, min(5, d))


def required_kind(interview_type: str, index: int) -> str:
    if interview_type == "mixed":
        return ["conceptual", "conceptual", "coding", "behavioral"][index % 4]
    return {"technical": "conceptual", "coding": "coding", "behavioral": "behavioral",
            "system_design": "system_design"}.get(interview_type, "conceptual")


def _fallback(index: int, difficulty: int) -> dict:
    question, topic, kind = FALLBACK_BANK[index % len(FALLBACK_BANK)]
    return {"question": question, "topic": topic, "difficulty": difficulty, "kind": kind}


def next_question(interview, turns: list, memory: dict) -> dict:
    index = len(turns)
    difficulty = target_difficulty(interview.level, turns)
    kind = required_kind(interview.interview_type, index)

    if not llm.enabled:
        return _fallback(index, difficulty)

    transcript = [
        {
            "question": t.question,
            "topic": t.topic,
            "answer": t.answer,
            "code": t.code,
            "score": (t.evaluation or {}).get("overall"),
            "feedback": (t.evaluation or {}).get("feedback"),
        }
        for t in turns[-6:]
    ]
    payload = {
        "candidate": {
            "role": interview.role,
            "level": interview.level,
            "focus": interview.focus or "general",
        },
        "interview_memory": {
            "known_weak_skills": memory.get("weak", []),
            "recently_improved": memory.get("improved", []),
            "note": "Probe weak skills when natural; do not repeat questions from earlier interviews.",
        },
        "question_number": index + 1,
        "target_difficulty": difficulty,
        "required_kind": kind,
        "previous_turns": transcript,
    }
    try:
        data = llm.complete_json(SYSTEM, json.dumps(payload))
        return {
            "question": str(data["question"]).strip(),
            "topic": str(data.get("topic", "general")).strip().lower()[:60] or "general",
            "difficulty": max(1, min(5, int(data.get("difficulty", difficulty)))),
            "kind": kind,
        }
    except Exception:  # network, quota, bad JSON: never break the interview
        log.exception("LLM question generation failed; using fallback")
        return _fallback(index, difficulty)
