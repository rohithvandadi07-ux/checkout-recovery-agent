"""
Audit logger for the checkout recovery agent.

Every recovery decision is recorded as one JSON object per line.
The logger records what happened but does not make decisions.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_AUDIT_PATH = Path("audit") / "decisions.jsonl"


def create_audit_record(
    session: dict[str, Any],
    diagnosis: dict[str, Any] | None,
    policy: dict[str, Any],
    execution: dict[str, Any],
) -> dict[str, Any]:
    """
    Create a structured audit record for one session.
    """

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session["session_id"],
        "diagnosis": (
            diagnosis["cause"]
            if diagnosis
            else None
        ),
        "confidence": (
            diagnosis["confidence"]
            if diagnosis
            else None
        ),
        "policy_decision": policy["decision"],
        "action": policy["action"],
        "execution_status": execution["execution_status"],
        "reason": policy["reason"],
        "execution_message": execution["execution_message"],
    }


def write_audit_record(
    record: dict[str, Any],
    audit_path: Path | None = None,
) -> None:
    """
    Append one audit record to the JSONL audit file.

    If no audit path is provided, the default project audit
    location is used.
    """

    if audit_path is None:
        audit_path = DEFAULT_AUDIT_PATH
    else:
        audit_path = Path(audit_path)

    audit_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with audit_path.open(
        "a",
        encoding="utf-8",
    ) as file:
        file.write(
            json.dumps(
                record,
                ensure_ascii=False,
            )
            + "\n"
        )


def log_session_decision(
    session: dict[str, Any],
    diagnosis: dict[str, Any] | None,
    policy: dict[str, Any],
    execution: dict[str, Any],
    audit_path: Path | None = None,
) -> dict[str, Any]:
    """
    Create and persist an audit record.

    If no audit path is provided, the default project audit
    location is used.

    Returns the record that was written.
    """

    record = create_audit_record(
        session=session,
        diagnosis=diagnosis,
        policy=policy,
        execution=execution,
    )

    write_audit_record(
        record=record,
        audit_path=audit_path,
    )

    return record


def read_audit_records(
    audit_path: Path | None = None,
) -> list[dict[str, Any]]:
    """
    Read all audit records from the JSONL file.

    If no audit path is provided, the default project audit
    location is used.
    """

    if audit_path is None:
        audit_path = DEFAULT_AUDIT_PATH
    else:
        audit_path = Path(audit_path)

    if not audit_path.exists():
        return []

    records = []

    with audit_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            records.append(
                json.loads(line)
            )

    return records