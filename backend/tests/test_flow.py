"""End-to-end smoke test using SQLite and the offline mock interviewer (no API key needed)."""
import os
import sys
from types import SimpleNamespace

os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["CELERY_EAGER"] = "true"
os.environ["ANTHROPIC_API_KEY"] = ""
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import interviewer, memory


def test_difficulty_adapts():
    strong = SimpleNamespace(evaluation={"overall": 9}, difficulty=3)
    weak = SimpleNamespace(evaluation={"overall": 3}, difficulty=3)
    assert interviewer.target_difficulty("mid", []) == 3
    assert interviewer.target_difficulty("mid", [strong]) == 4
    assert interviewer.target_difficulty("mid", [weak]) == 2


def test_memory_insights():
    skills = memory.summarize({"sql": [4.0, 7.0], "indexing": [5.0]})
    text = " ".join(memory.make_insights(skills))
    assert "improved in sql" in text
    assert "Indexing remains an area to practice" in text


def test_full_interview_flow():
    with TestClient(app) as c:
        email = "tester@example.com"
        c.post("/api/auth/register", json={"email": email, "password": "password123"})
        token = c.post("/api/auth/login", data={"username": email, "password": "password123"}).json()["access_token"]
        h = {"Authorization": f"Bearer {token}"}

        iv = c.post("/api/interviews", headers=h, json={"role": "Backend", "level": "mid", "interview_type": "mixed"}).json()
        assert len(iv["turns"]) == 1

        with c.websocket_connect(f"/ws/interviews/{iv['id']}?token={token}") as ws:
            assert ws.receive_json()["type"] == "state"
            ws.send_json({"type": "answer", "text": "Async code does not block the main flow, it yields while waiting on I/O. " * 3})
            assert ws.receive_json()["type"] == "evaluation"
            assert ws.receive_json()["type"] == "question"

        done = c.post(f"/api/interviews/{iv['id']}/finish", headers=h).json()
        assert done["status"] == "completed"
        assert done["report"]["skill_scores"]

        prof = c.get("/api/profile", headers=h).json()
        assert prof["interviews_completed"] == 1 and prof["skills"]

        run = c.post("/api/code/run", headers=h, json={"code": "print(2+2)"}).json()
        assert run["stdout"].strip() == "4"


@pytest.fixture(autouse=True, scope="module")
def cleanup():
    yield
    if os.path.exists("test.db"):
        os.remove("test.db")
