"""Real-time interview channel.

Client -> server: {"type": "answer", "text": str, "code": str | null}
Server -> client: state | evaluation | question | done | error
"""
import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .. import models, schemas
from ..config import settings
from ..database import SessionLocal
from ..deps import user_from_token
from ..services import session

router = APIRouter()


def _dump(turn: models.Turn) -> dict:
    return schemas.TurnOut.model_validate(turn).model_dump(mode="json")


def _load_state(interview_id: int, token: str) -> dict | None:
    db = SessionLocal()
    try:
        user = user_from_token(db, token)
        interview = db.get(models.Interview, interview_id)
        if not user or not interview or interview.user_id != user.id:
            return None
        return {
            "type": "state",
            "status": interview.status,
            "max_questions": settings.max_questions,
            "turns": [_dump(t) for t in session.get_turns(db, interview_id)],
        }
    finally:
        db.close()


def _handle_answer(interview_id: int, text: str, code: str | None) -> list[dict]:
    """Blocking work (LLM calls) runs in a worker thread with its own DB session."""
    db = SessionLocal()
    try:
        interview = db.get(models.Interview, interview_id)
        turn, nxt = session.submit_answer(db, interview, text, code)
        events = [{"type": "evaluation", "turn_index": turn.index, "evaluation": turn.evaluation}]
        events.append({"type": "question", "turn": _dump(nxt)} if nxt else {"type": "done"})
        return events
    finally:
        db.close()


@router.websocket("/ws/interviews/{interview_id}")
async def interview_socket(ws: WebSocket, interview_id: int, token: str):
    state = await asyncio.to_thread(_load_state, interview_id, token)
    if state is None:
        await ws.close(code=4401)
        return
    await ws.accept()
    await ws.send_json(state)
    try:
        while True:
            msg = await ws.receive_json()
            if msg.get("type") != "answer" or not str(msg.get("text", "")).strip():
                await ws.send_json({"type": "error", "detail": "Send {type: 'answer', text: ...}"})
                continue
            try:
                events = await asyncio.to_thread(
                    _handle_answer, interview_id, msg["text"][:8000], (msg.get("code") or None)
                )
            except ValueError as exc:
                await ws.send_json({"type": "error", "detail": str(exc)})
                continue
            for event in events:
                await ws.send_json(event)
    except WebSocketDisconnect:
        pass
