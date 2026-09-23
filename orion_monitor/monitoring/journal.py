from collections.abc import Iterator
from dataclasses import dataclass
import re
import subprocess
import time

ERROR_MARKERS = ("ERROR", "CRITICAL", "Traceback", "Exception")
TRACEBACK_START = "Traceback (most recent call last):"
TRACEBACK_CONTINUATION_SECONDS = 1.0
_JOURNAL_PREFIX = re.compile(r"^\S+\s+\S+\s+[^:]+:\s*")

@dataclass(frozen=True)
class JournalEvent:
    unit: str
    text: str

    @property
    def fingerprint_text(self) -> str:
        return "\n".join(_JOURNAL_PREFIX.sub("", line, count=1) for line in self.text.splitlines())

def recent_logs(unit: str, lines: int = 30) -> str:
    result = subprocess.run(
        ["journalctl", "-u", unit, "-n", str(lines), "--no-pager", "-o", "short-iso"],
        check=False, capture_output=True, text=True, timeout=10,
    )
    return result.stdout.strip() or "Log is empty."

def recent_errors(unit: str, lines: int = 500, limit: int = 20) -> list[str]:
    text = recent_logs(unit, lines)
    return [line for line in text.splitlines() if any(m in line for m in ERROR_MARKERS)][-limit:]

def _read_traceback(process: subprocess.Popen[str], first_line: str) -> str:
    assert process.stdout is not None
    collected = [first_line]
    deadline = time.monotonic() + TRACEBACK_CONTINUATION_SECONDS
    while time.monotonic() < deadline:
        next_line = process.stdout.readline()
        if not next_line:
            break
        line = next_line.rstrip()
        collected.append(line)
        if line and not line.startswith((" ", "\t")) and ("Error:" in line or "Exception:" in line):
            break
        deadline = time.monotonic() + TRACEBACK_CONTINUATION_SECONDS
    return "\n".join(collected)

def follow_errors(unit: str) -> Iterator[JournalEvent]:
    process = subprocess.Popen(
        ["journalctl", "-u", unit, "-f", "-n", "0", "--no-pager", "-o", "short-iso"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1,
    )
    assert process.stdout is not None
    pending_error: str | None = None
    for raw_line in process.stdout:
        line = raw_line.rstrip()
        if pending_error is not None:
            if TRACEBACK_START in line:
                yield JournalEvent(unit, f"{pending_error}\n{_read_traceback(process, line)}")
                pending_error = None
                continue
            yield JournalEvent(unit, pending_error)
            pending_error = None
        if ("ERROR" in line or "CRITICAL" in line) and TRACEBACK_START in line:
            pending_error = line
        elif "ERROR" in line or "CRITICAL" in line:
            yield JournalEvent(unit, line)
        elif TRACEBACK_START in line:
            yield JournalEvent(unit, _read_traceback(process, line))
        elif "Exception" in line:
            yield JournalEvent(unit, line)
    if pending_error is not None:
        yield JournalEvent(unit, pending_error)
