"""
In-memory state for the current/last retrain job.

The trainer pushes log lines and progress here; the FastAPI /training-status
endpoint reads from it; the Angular UI polls /training-status every ~1.5s.

Single-process design — fine for the current single-worker FastAPI deployment.
"""
import threading
from collections import deque
from datetime import datetime
from typing import Literal, Optional

Status = Literal["idle", "running", "complete", "failed"]
_MAX_LOG_LINES = 500

_lock = threading.Lock()
_state = {
    "status": "idle",
    "progress": 0,
    "current_run_id": None,
    "started_at": None,
    "ended_at": None,
    "error": None,
    "logs": deque(maxlen=_MAX_LOG_LINES),
}


def _now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def _stamp(line: str) -> str:
    return f"[{datetime.now().strftime('%H:%M:%S')}] {line}"


def get_state() -> dict:
    with _lock:
        return {
            "status": _state["status"],
            "progress": _state["progress"],
            "current_run_id": _state["current_run_id"],
            "started_at": _state["started_at"],
            "ended_at": _state["ended_at"],
            "error": _state["error"],
            "logs": list(_state["logs"]),
        }


def is_running() -> bool:
    with _lock:
        return _state["status"] == "running"


def start(run_id: str) -> None:
    with _lock:
        _state["status"] = "running"
        _state["progress"] = 0
        _state["current_run_id"] = run_id
        _state["started_at"] = _now()
        _state["ended_at"] = None
        _state["error"] = None
        _state["logs"].clear()
        _state["logs"].append(_stamp(f"Initiating training job (run {run_id})..."))


def push_log(line: str) -> None:
    with _lock:
        _state["logs"].append(_stamp(line))


def set_progress(value: int) -> None:
    with _lock:
        _state["progress"] = max(0, min(100, int(value)))


def complete() -> None:
    with _lock:
        _state["status"] = "complete"
        _state["progress"] = 100
        _state["ended_at"] = _now()
        _state["logs"].append(_stamp("✓ Model trained successfully!"))


def fail(error: str) -> None:
    with _lock:
        _state["status"] = "failed"
        _state["ended_at"] = _now()
        _state["error"] = error
        _state["logs"].append(_stamp(f"✗ Training failed: {error}"))


def reset() -> None:
    with _lock:
        _state["status"] = "idle"
        _state["progress"] = 0
        _state["current_run_id"] = None
        _state["started_at"] = None
        _state["ended_at"] = None
        _state["error"] = None
        _state["logs"].clear()
