"""Run candidate code.

DEV-ONLY SANDBOX: a resource-limited subprocess is NOT a security boundary. Before exposing this
publicly, run code in an isolated container/microVM (e.g. gVisor, Firecracker, Judge0) with no network.
"""
import subprocess
import sys
import tempfile

from fastapi import APIRouter, Depends

from .. import models, schemas
from ..config import settings
from ..deps import get_current_user

try:
    import resource
except ImportError:  # Windows
    resource = None

router = APIRouter(prefix="/api/code", tags=["code"])


def _limits() -> None:
    if resource:
        t = settings.code_timeout_seconds
        resource.setrlimit(resource.RLIMIT_CPU, (t, t))
        resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024,) * 2)
        resource.setrlimit(resource.RLIMIT_FSIZE, (1024 * 1024,) * 2)


@router.post("/run", response_model=schemas.CodeRunOut)
def run_code(data: schemas.CodeRunIn, user: models.User = Depends(get_current_user)):
    with tempfile.TemporaryDirectory() as cwd:
        try:
            proc = subprocess.run(
                [sys.executable, "-I", "-c", data.code],
                capture_output=True,
                text=True,
                timeout=settings.code_timeout_seconds,
                cwd=cwd,
                env={},
                preexec_fn=_limits if resource else None,
            )
        except subprocess.TimeoutExpired:
            return schemas.CodeRunOut(stdout="", stderr="Timed out", exit_code=-1, timed_out=True)
    return schemas.CodeRunOut(
        stdout=proc.stdout[:10000], stderr=proc.stderr[:10000], exit_code=proc.returncode, timed_out=False
    )
