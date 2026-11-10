from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import Base, engine
from .routers import auth, code, interviews, profile, ws
from .services.llm import llm


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)  # swap for Alembic migrations once the schema stabilises
    yield


app = FastAPI(title="InterviewIQ API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (auth.router, interviews.router, profile.router, code.router, ws.router):
    app.include_router(r)


@app.get("/api/health")
def health():
    return {"status": "ok", "llm": "anthropic" if llm.enabled else "offline-mock"}
