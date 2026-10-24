"""The debug trace is off by default and writes only to the configured path."""
import json

from src.utils.debug_log import ENV_VAR, debug_log


def test_debug_log_off_by_default(monkeypatch, tmp_path):
    monkeypatch.delenv(ENV_VAR, raising=False)
    monkeypatch.chdir(tmp_path)
    called = []
    debug_log(lambda: called.append(1) or {"message": "x"})
    assert called == []
    assert list(tmp_path.iterdir()) == []


def test_debug_log_writes_to_relative_path(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv(ENV_VAR, "logs/debug.log")
    debug_log(lambda: {"message": "hello"})
    entry = json.loads((tmp_path / "logs" / "debug.log").read_text().strip())
    assert entry["message"] == "hello" and "timestamp" in entry


def test_debug_log_never_raises(monkeypatch, tmp_path):
    monkeypatch.setenv(ENV_VAR, str(tmp_path / "d.log"))
    debug_log(lambda: 1 / 0)
