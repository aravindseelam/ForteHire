import os
from datetime import date
import pandas as pd

from database import get_db
from priority import score_action

OUT_DIR = "data"
STAGE_ORDER = {
    "Applied": 1,
    "Shortlisted": 2,
    "Interview": 3,
    "Offer": 4,
    "Hired": 5,
    "Rejected": 6,
}

ACTIONS_SQL = """
SELECT a.action_id, a.application_id, a.action_type, a.description,
       a.created_at, a.due_at, a.status, a.completed_at,
       a.assigned_recruiter_id, r.name AS recruiter,
       c.candidate_id, c.name AS candidate, c.location AS candidate_location,
       j.job_id, j.job_title, j.company, j.priority AS job_priority,
       ap.stage, ap.last_activity_at, ap.feedback_status
FROM actions a
JOIN applications ap ON ap.application_id = a.application_id
JOIN candidates c ON c.candidate_id = ap.candidate_id
JOIN jobs j ON j.job_id = ap.job_id
JOIN recruiters r ON r.recruiter_id = a.assigned_recruiter_id
"""

APPLICATIONS_SQL = """
SELECT ap.application_id, ap.candidate_id, ap.job_id, ap.recruiter_id,
       r.name AS recruiter, ap.stage, ap.applied_at, ap.last_activity_at,
       ap.feedback_status
FROM applications ap
JOIN recruiters r ON r.recruiter_id = ap.recruiter_id
"""


def _to_date(val: str) -> date:
    return date.fromisoformat(val[:10])


def export():
    os.makedirs(OUT_DIR, exist_ok=True)
    conn = get_db()
    today = date.today()

    # 1. Actions (denormalized fact table for KPI cards & recruiter workload)
    actions_df = pd.read_sql_query(ACTIONS_SQL, conn)
    scores, labels, overdue_flags, age_days, on_time_flags = [], [], [], [], []

    for row in actions_df.itertuples(index=False):
        due = _to_date(row.due_at)
        created = _to_date(row.created_at)
        last_act = _to_date(row.last_activity_at)

        score, label, _ = score_action(
            due, last_act, row.job_priority, row.feedback_status, today
        )
        scores.append(score)
        labels.append(label)
        overdue_flags.append(row.status == "Pending" and due < today)
        age_days.append(max((today - created).days, 0))
        on_time_flags.append(
            row.status == "Completed"
            and pd.notna(row.completed_at)
            and _to_date(str(row.completed_at)) <= due
        )

    actions_df["priority_score"] = scores
    actions_df["priority_label"] = labels
    actions_df["is_overdue"] = overdue_flags
    actions_df["age_days"] = age_days
    actions_df["completed_on_time"] = on_time_flags
    actions_df["stage_order"] = actions_df["stage"].map(STAGE_ORDER)
    actions_df["snapshot_date"] = today.isoformat()
    actions_df.to_csv(os.path.join(OUT_DIR, "actions.csv"), index=False)

    # 2. Applications (for accurate stage Funnel without double-counting)
    apps_df = pd.read_sql_query(APPLICATIONS_SQL, conn)
    apps_df["stage_order"] = apps_df["stage"].map(STAGE_ORDER)
    apps_df.to_csv(os.path.join(OUT_DIR, "applications.csv"), index=False)

    # 3. Dimension tables
    candidates_df = pd.read_sql_query("SELECT * FROM candidates", conn)
    candidates_df.to_csv(os.path.join(OUT_DIR, "candidates.csv"), index=False)

    jobs_df = pd.read_sql_query("SELECT * FROM jobs", conn)
    jobs_df.to_csv(os.path.join(OUT_DIR, "jobs.csv"), index=False)

    conn.close()
    print(
        f"Exported to {OUT_DIR}/: "
        f"actions ({len(actions_df)}), applications ({len(apps_df)}), "
        f"candidates ({len(candidates_df)}), jobs ({len(jobs_df)})"
    )


if __name__ == "__main__":
    export()