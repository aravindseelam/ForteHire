from datetime import date, datetime, timedelta
from flask import Flask, abort, jsonify, render_template, request
import pandas as pd

from database import get_db, init_db
from priority import format_reasons, score_action

app = Flask(__name__)

STAGES = ["Applied", "Shortlisted", "Interview", "Offer", "Hired", "Rejected"]

QUEUE_SQL = """
SELECT a.action_id, a.action_type, a.description, a.created_at, a.due_at,
       a.status, a.completed_at, a.assigned_recruiter_id,
       c.candidate_id, c.name AS candidate,
       j.job_id, j.job_title, j.company, j.priority AS job_priority,
       ap.application_id, ap.stage, ap.last_activity_at, ap.feedback_status,
       r.name AS recruiter
FROM actions a
JOIN applications ap ON ap.application_id = a.application_id
JOIN candidates c ON c.candidate_id = ap.candidate_id
JOIN jobs j ON j.job_id = ap.job_id
JOIN recruiters r ON r.recruiter_id = a.assigned_recruiter_id
"""


def _parse_iso_date(value: str) -> date:
    return date.fromisoformat(value[:10])


def load_queue():
    conn = get_db()
    rows = [dict(r) for r in conn.execute(QUEUE_SQL)]
    conn.close()

    today = date.today()
    for r in rows:
        due = _parse_iso_date(r["due_at"])
        created = _parse_iso_date(r["created_at"])
        last = _parse_iso_date(r["last_activity_at"])

        score, label, reasons = score_action(
            due, last, r["job_priority"], r["feedback_status"], today
        )
        r["score"] = score
        r["priority"] = label
        r["reasons"] = reasons
        r["reasons_text"] = format_reasons(reasons)
        r["waiting_days"] = (today - last).days
        r["age_days"] = max((today - created).days, 0)
        r["is_overdue"] = r["status"] == "Pending" and due < today
        r["is_today"] = r["status"] == "Pending" and due == today
        r["completed_on_time"] = (
            r["status"] == "Completed"
            and bool(r["completed_at"])
            and _parse_iso_date(r["completed_at"]) <= due
        )
    return rows


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

@app.route("/")
def dashboard():
    q = load_queue()
    pending = [r for r in q if r["status"] == "Pending"]

    conn = get_db()
    kpi = {
        "active_jobs": conn.execute(
            "SELECT COUNT(*) FROM jobs WHERE status='Open'"
        ).fetchone()[0],
        "candidates": conn.execute("SELECT COUNT(*) FROM candidates").fetchone()[0],
        "pending": len(pending),
        "overdue": sum(r["is_overdue"] for r in pending),
        "interviews": conn.execute(
            "SELECT COUNT(*) FROM applications WHERE stage='Interview'"
        ).fetchone()[0],
        "offers": conn.execute(
            "SELECT COUNT(*) FROM applications WHERE stage='Offer'"
        ).fetchone()[0],
    }

    stage_rows = conn.execute(
        "SELECT stage, COUNT(*) AS cnt FROM applications GROUP BY stage"
    ).fetchall()
    conn.close()

    stage_map = {r["stage"]: r["cnt"] for r in stage_rows}
    stage_counts = [stage_map.get(s, 0) for s in STAGES]

    today = date.today()
    days = [(today - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
    activity_7d = {
        "labels": [d[5:] for d in days],  # MM-DD
        "created": [
            sum(1 for r in q if r["created_at"][:10] == d)
            for d in days
        ],
        "completed": [
            sum(1 for r in q if r["completed_at"] and r["completed_at"][:10] == d)
            for d in days
        ],
    }

    by_priority = {
        p: sum(r["priority"] == p for r in pending) for p in ("High", "Medium", "Low")
    }
    top = sorted(pending, key=lambda r: (-r["score"], r["due_at"]))[:5]

    return render_template(
        "dashboard.html",
        kpi=kpi,
        by_priority=by_priority,
        top=top,
        stages=STAGES,
        stage_counts=stage_counts,
        activity_7d=activity_7d,
    )


@app.route("/queue")
def action_queue():
    f = request.args.get("filter", "all")
    q = load_queue()
    pending = [r for r in q if r["status"] == "Pending"]

    views = {
        "all": pending,
        "high": [r for r in pending if r["priority"] == "High"],
        "medium": [r for r in pending if r["priority"] == "Medium"],
        "low": [r for r in pending if r["priority"] == "Low"],
        "overdue": [r for r in pending if r["is_overdue"]],
        "today": [r for r in pending if r["is_today"]],
        "completed": [r for r in q if r["status"] == "Completed"],
    }
    rows = sorted(views.get(f, pending), key=lambda r: (-r["score"], r["due_at"]))

    conn = get_db()
    recruiters = [dict(r) for r in conn.execute(
        "SELECT recruiter_id, name FROM recruiters ORDER BY name"
    )]
    applications = [dict(r) for r in conn.execute("""
        SELECT ap.application_id, c.name AS candidate, j.job_title
        FROM applications ap
        JOIN candidates c ON c.candidate_id = ap.candidate_id
        JOIN jobs j ON j.job_id = ap.job_id
        ORDER BY c.name
    """)]
    conn.close()

    return render_template(
        "action_queue.html",
        rows=rows,
        active=f,
        stages=STAGES,
        recruiters=recruiters,
        applications=applications,
    )


@app.route("/pipeline")
def pipeline():
    conn = get_db()
    rows = [dict(r) for r in conn.execute("""
        SELECT ap.application_id, ap.stage, ap.applied_at, ap.last_activity_at,
               ap.feedback_status, c.candidate_id, c.name AS candidate,
               j.job_id, j.job_title, j.company, j.priority AS job_priority,
               r.name AS recruiter,
               COALESCE(SUM(CASE WHEN a.status = 'Pending' THEN 1 ELSE 0 END), 0) AS open_actions
        FROM applications ap
        JOIN candidates c ON c.candidate_id = ap.candidate_id
        JOIN jobs j ON j.job_id = ap.job_id
        JOIN recruiters r ON r.recruiter_id = ap.recruiter_id
        LEFT JOIN actions a ON a.application_id = ap.application_id
        GROUP BY ap.application_id
        ORDER BY ap.last_activity_at ASC
    """)]
    conn.close()

    today = date.today()
    grouped = {stage: [] for stage in STAGES}
    for r in rows:
        r["waiting_days"] = (today - _parse_iso_date(r["last_activity_at"])).days
        grouped[r["stage"]].append(r)

    return render_template("pipeline.html", grouped=grouped, stages=STAGES)


@app.route("/candidates")
def candidates_list():
    conn = get_db()
    rows = [dict(r) for r in conn.execute("""
        SELECT c.*, COUNT(ap.application_id) AS app_count,
               MAX(ap.last_activity_at) AS last_activity_at
        FROM candidates c
        LEFT JOIN applications ap ON ap.candidate_id = c.candidate_id
        GROUP BY c.candidate_id
        ORDER BY c.name
    """)]
    conn.close()
    return render_template("candidates.html", candidates=rows)


@app.route("/candidates/<int:candidate_id>")
def candidate_detail(candidate_id):
    conn = get_db()
    candidate = conn.execute(
        "SELECT * FROM candidates WHERE candidate_id=?", (candidate_id,)
    ).fetchone()
    if not candidate:
        conn.close()
        abort(404)

    apps = [dict(r) for r in conn.execute("""
        SELECT ap.*, j.job_title, j.company, j.priority AS job_priority,
               r.name AS recruiter
        FROM applications ap
        JOIN jobs j ON j.job_id = ap.job_id
        JOIN recruiters r ON r.recruiter_id = ap.recruiter_id
        WHERE ap.candidate_id=?
        ORDER BY ap.applied_at DESC
    """, (candidate_id,))]

    history = [dict(r) for r in conn.execute("""
        SELECT sh.from_stage, sh.to_stage, sh.changed_at, j.job_title
        FROM stage_history sh
        JOIN applications ap ON ap.application_id = sh.application_id
        JOIN jobs j ON j.job_id = ap.job_id
        WHERE ap.candidate_id=?
        ORDER BY sh.changed_at DESC
    """, (candidate_id,))]

    recruiters = [dict(r) for r in conn.execute(
        "SELECT recruiter_id, name FROM recruiters ORDER BY name"
    )]
    conn.close()

    cand_actions = [r for r in load_queue() if r["candidate_id"] == candidate_id]
    cand_actions.sort(key=lambda r: (r["status"] == "Completed", -r["score"], r["due_at"]))

    activity = []
    for h in history:
        label = (
            f"Moved {h['from_stage']} -> {h['to_stage']}"
            if h["from_stage"]
            else f"Applied ({h['to_stage']})"
        )
        activity.append({
            "timestamp": h["changed_at"],
            "kind": "stage",
            "title": label,
            "detail": h["job_title"],
        })
    for a in cand_actions:
        if a["status"] == "Completed" and a["completed_at"]:
            activity.append({
                "timestamp": a["completed_at"],
                "kind": "action_done",
                "title": f"Completed: {a['action_type']}",
                "detail": f"{a['job_title']} ({a['recruiter']})",
            })
        else:
            activity.append({
                "timestamp": a["created_at"],
                "kind": "action_open",
                "title": f"Task created: {a['action_type']} (due {a['due_at']})",
                "detail": f"{a['job_title']} ({a['recruiter']})",
            })
    activity.sort(key=lambda item: item["timestamp"], reverse=True)

    return render_template(
        "candidate_detail.html",
        candidate=dict(candidate),
        applications=apps,
        actions=cand_actions,
        activity=activity,
        stages=STAGES,
        recruiters=recruiters,
    )


@app.route("/jobs")
def jobs():
    today_iso = date.today().isoformat()
    conn = get_db()
    rows = [dict(r) for r in conn.execute("""
        SELECT j.*,
               COUNT(DISTINCT ap.application_id) AS applicant_count,
               SUM(CASE WHEN ap.stage = 'Interview' THEN 1 ELSE 0 END) AS interview_count,
               SUM(CASE WHEN ap.stage = 'Offer' THEN 1 ELSE 0 END) AS offer_count,
               (
                   SELECT COUNT(*)
                   FROM actions a
                   JOIN applications ap2 ON ap2.application_id = a.application_id
                   WHERE ap2.job_id = j.job_id
                     AND a.status = 'Pending'
                     AND a.due_at < ?
               ) AS overdue_actions
        FROM jobs j
        LEFT JOIN applications ap ON ap.job_id = j.job_id
        GROUP BY j.job_id
        ORDER BY
            CASE j.priority
                WHEN 'Critical' THEN 1
                WHEN 'High' THEN 2
                WHEN 'Normal' THEN 3
                ELSE 4
            END,
            j.target_fill_date ASC
    """, (today_iso,))]
    conn.close()
    return render_template("jobs.html", jobs=rows)


@app.route("/analytics")
def analytics():
    rec = request.args.get("recruiter", "").strip()
    start = request.args.get("start", "").strip()
    end = request.args.get("end", "").strip()

    conn = get_db()
    recruiters = [dict(r) for r in conn.execute(
        "SELECT recruiter_id, name FROM recruiters ORDER BY name"
    )]
    conn.close()

    rows = load_queue()
    df = pd.DataFrame(rows)

    if not df.empty:
        if rec.isdigit():
            df = df[df["assigned_recruiter_id"] == int(rec)]
        if start:
            try:
                _parse_iso_date(start)
                df = df[df["due_at"] >= start]
            except ValueError:
                start = ""
        if end:
            try:
                _parse_iso_date(end)
                df = df[df["due_at"] <= end]
            except ValueError:
                end = ""

    if df.empty:
        metrics = {
            "total_actions": 0,
            "open_actions": 0,
            "overdue_rate": 0.0,
            "completion_rate": 0.0,
            "on_time_rate": 0.0,
            "avg_action_age": 0.0,
            "workload": {},
            "by_priority": {"High": 0, "Medium": 0, "Low": 0},
        }
    else:
        open_ = df[df["status"] == "Pending"]
        done_ = df[df["status"] == "Completed"]
        metrics = {
            "total_actions": int(len(df)),
            "open_actions": int(len(open_)),
            "overdue_rate": round(100 * open_["is_overdue"].mean(), 1) if len(open_) else 0.0,
            "completion_rate": round(100 * (df["status"] == "Completed").mean(), 1),
            "on_time_rate": (
                round(100 * done_["completed_on_time"].mean(), 1) if len(done_) else 0.0
            ),
            "avg_action_age": round(float(open_["age_days"].mean()), 1) if len(open_) else 0.0,
            "workload": open_.groupby("recruiter").size().to_dict(),
            "by_priority": {
                p: int((open_["priority"] == p).sum()) for p in ("High", "Medium", "Low")
            },
        }

    return render_template(
        "analytics.html",
        m=metrics,
        recruiters=recruiters,
        selected_recruiter=rec,
        start=start,
        end=end,
    )


# ---------------------------------------------------------------------------
# Mutations (JSON API)
# ---------------------------------------------------------------------------

@app.post("/actions/<int:aid>/complete")
def complete(aid):
    conn = get_db()
    cur = conn.execute(
        "UPDATE actions SET status='Completed', completed_at=? WHERE action_id=?",
        (datetime.now().isoformat(timespec="seconds"), aid),
    )
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        return jsonify(error="Action not found"), 404
    return jsonify(ok=True)


@app.post("/actions/<int:aid>/snooze")
def snooze(aid):
    days = request.form.get("days", "1")
    try:
        delta = max(1, min(int(days), 14))
    except ValueError:
        return jsonify(error="Invalid snooze days"), 400

    conn = get_db()
    row = conn.execute(
        "SELECT due_at FROM actions WHERE action_id=?", (aid,)
    ).fetchone()
    if not row:
        conn.close()
        return jsonify(error="Action not found"), 404

    base = max(_parse_iso_date(row["due_at"]), date.today())
    new_due = (base + timedelta(days=delta)).isoformat()
    conn.execute("UPDATE actions SET due_at=? WHERE action_id=?", (new_due, aid))
    conn.commit()
    conn.close()
    return jsonify(ok=True, due_at=new_due)


@app.post("/applications/<int:app_id>/stage")
def change_stage(app_id):
    new_stage = request.form.get("stage", "").strip()
    if new_stage not in STAGES:
        return jsonify(error=f"Invalid stage. Must be one of: {', '.join(STAGES)}"), 400

    conn = get_db()
    row = conn.execute(
        "SELECT stage FROM applications WHERE application_id=?", (app_id,)
    ).fetchone()
    if not row:
        conn.close()
        return jsonify(error="Application not found"), 404

    old_stage = row["stage"]
    if old_stage != new_stage:
        now = datetime.now().isoformat(timespec="seconds")
        conn.execute(
            "UPDATE applications SET stage=?, last_activity_at=? WHERE application_id=?",
            (new_stage, now[:10], app_id),
        )
        conn.execute(
            "INSERT INTO stage_history(application_id, from_stage, to_stage, changed_at) VALUES(?,?,?,?)",
            (app_id, old_stage, new_stage, now),
        )
        conn.commit()
    conn.close()
    return jsonify(ok=True, stage=new_stage)


@app.post("/tasks")
def create_task():
    f = request.form
    required = ["application_id", "action_type", "due_at", "assigned_recruiter_id"]
    if any(not f.get(k, "").strip() for k in required):
        return jsonify(error="Missing required field"), 400

    today = date.today()
    try:
        due_dt = _parse_iso_date(f["due_at"].strip())
    except ValueError:
        return jsonify(error="Invalid due_at date (expected YYYY-MM-DD)"), 400

    if due_dt < today:
        return jsonify(error="due_at cannot be earlier than created_at (today)"), 400

    try:
        app_id = int(f["application_id"])
        recruiter_id = int(f["assigned_recruiter_id"])
    except ValueError:
        return jsonify(error="application_id and assigned_recruiter_id must be integers"), 400

    conn = get_db()
    app_row = conn.execute("""
        SELECT ap.last_activity_at, ap.feedback_status, j.priority AS job_priority
        FROM applications ap
        JOIN jobs j ON j.job_id = ap.job_id
        WHERE ap.application_id=?
    """, (app_id,)).fetchone()
    if not app_row:
        conn.close()
        return jsonify(error="Unknown application_id"), 400

    rec_row = conn.execute(
        "SELECT 1 FROM recruiters WHERE recruiter_id=?", (recruiter_id,)
    ).fetchone()
    if not rec_row:
        conn.close()
        return jsonify(error="Unknown assigned_recruiter_id"), 400

    score, _, _ = score_action(
        due_dt,
        _parse_iso_date(app_row["last_activity_at"]),
        app_row["job_priority"],
        app_row["feedback_status"],
        today,
    )

    cur = conn.execute("""
        INSERT INTO actions
            (application_id, action_type, description, created_at, due_at,
             priority_score, assigned_recruiter_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        app_id,
        f["action_type"].strip(),
        f.get("description", "").strip(),
        today.isoformat(),
        due_dt.isoformat(),
        score,
        recruiter_id,
    ))
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return jsonify(ok=True, action_id=new_id, priority_score=score), 201


if __name__ == "__main__":
    init_db()
    app.run(debug=True)