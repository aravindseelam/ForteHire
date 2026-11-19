from datetime import date, datetime
from typing import List, Optional, Tuple, Union

DateLike = Union[date, datetime, str]


def _to_date(value: DateLike) -> date:
    """Normalize a date, datetime, or ISO-8601 string (YYYY-MM-DD...) to a date."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value[:10])
    raise TypeError(f"Unsupported date value: {value!r}")


def score_action(
    due_at: DateLike,
    last_activity_at: DateLike,
    job_priority: str,
    feedback_status: str,
    today: Optional[DateLike] = None,
) -> Tuple[int, str, List[Tuple[str, int]]]:
    """
    Compute deterministic task urgency (0–45) with human-readable reasons.
    Ranks workflow actions—never candidates.
    """
    ref_day = _to_date(today) if today is not None else date.today()
    due_day = _to_date(due_at)
    last_act_day = _to_date(last_activity_at)

    reasons: List[Tuple[str, int]] = []

    # D: Due date urgency (0–15)
    overdue = (ref_day - due_day).days
    if overdue > 3:
        d, r = 15, f"{overdue} days overdue"
    elif overdue >= 1:
        unit = "day" if overdue == 1 else "days"
        d, r = 12, f"{overdue} {unit} overdue"
    elif overdue == 0:
        d, r = 9, "Due today"
    elif overdue == -1:
        d, r = 6, "Due tomorrow"
    else:
        d, r = 0, None
    if r:
        reasons.append((r, d))

    # W: Waiting time since last activity (0–10)
    waiting = (ref_day - last_act_day).days
    if waiting >= 5:
        w = 10
    elif waiting >= 3:
        w = 6
    else:
        w = 0
    if w:
        reasons.append((f"Waiting {waiting} days", w))

    # J: Job importance (0–10)
    if job_priority in ("High", "Critical"):
        j = 10
    elif job_priority == "Normal":
        j = 5
    else:
        j = 0
    if j:
        reasons.append((f"{job_priority} priority job", j))

    # B: Hiring-manager feedback blocker (0–10)
    b = 10 if feedback_status == "Pending" else 0
    if b:
        reasons.append(("Feedback pending", b))

    total = d + w + j + b
    label = "High" if total >= 32 else "Medium" if total >= 18 else "Low"
    return total, label, reasons


def format_reasons(reasons: List[Tuple[str, int]]) -> str:
    """Format score breakdown for the Action Queue detail panel."""
    if not reasons:
        return "No urgency factors active"
    return ", ".join(f"+{pts} {text}" for text, pts in reasons)