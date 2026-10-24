"""Opt-in JSON-lines debug trace.

Off by default. Set MEDIA_ASSISTANT_DEBUG_LOG to a file path (relative paths resolve
against the current directory) to append one JSON object per traced event.
"""
import json
import os
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional

ENV_VAR = "MEDIA_ASSISTANT_DEBUG_LOG"


def debug_log_path() -> Optional[Path]:
    """Return the configured debug log path, or None when tracing is off."""
    value = os.getenv(ENV_VAR, "").strip()
    return Path(value).expanduser() if value else None


def debug_log(build_entry: Callable[[], Dict[str, Any]]) -> None:
    """Append the entry returned by *build_entry* when tracing is enabled.

    The builder is only called when tracing is on, and any error while building or
    writing the entry is ignored so tracing can never break a run.
    """
    path = debug_log_path()
    if path is None:
        return
    try:
        entry = build_entry()
        entry.setdefault("timestamp", time.time())
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass
