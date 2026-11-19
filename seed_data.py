import random
from datetime import date, timedelta

from database import get_db, init_db
from priority import score_action

random.seed(42)
TODAY = date.today()


def iso(offset_days: int) -> str:
    return (TODAY + timedelta(days=offset_days)).isoformat()


RECRUITERS = [
    (1, "Ananya Iyer", "ananya@hirepulse.demo", "Senior Recruiter"),
    (2, "Rohan Mehta", "rohan@hirepulse.demo", "Technical Recruiter"),
    (3, "Priya Nair", "priya@hirepulse.demo", "Recruiter"),
]

JOBS = [
    (1, "Python Developer", "FinEdge Labs", "High", "Open", iso(14)),
    (2, "Frontend Engineer", "CloudCart", "Critical", "Open", iso(7)),
    (3, "Data Analyst", "MetricFlow", "Normal", "Open", iso(21)),
    (4, "DevOps Engineer", "ScaleGrid", "High", "Open", iso(18)),
    (5, "QA Automation Engineer", "VeriStack", "Low", "Open", iso(30)),
]

CANDIDATE_NAMES = [
    "Rahul Sharma", "Aditi Verma", "Vikram Singh", "Sneha Kulkarni", "Arjun Reddy",
    "Meera Joshi", "Karthik Rao", "Neha Gupta", "Siddharth Jain", "Pooja Menon",
    "Nikhil Das", "Divya Kapoor", "Varun Malhotra", "Ritika Bose", "Abhishek Tiwari",
    "Tanvi Deshmukh", "Pranav Shetty", "Komal Agarwal", "Harshvardhan Patel", "Shreya Sen",
    "Deepak Chawla", "Ishita Roy", "Manish Yadav", "Anjali Pillai", "Gaurav Mishra",
    "Swati Bansal", "Rishabh Saxena", "Kavya Krishnan", "Tushar Khanna", "Nandini Bhatt",
]

LOCATIONS = ["Bengaluru", "Hyderabad", "Pune", "Mumbai", "Delhi NCR", "Chennai"]

STAGE_ORDER = ["Applied", "Shortlisted", "Interview", "Offer", "Hired"]

ACTION_TEMPLATES = [
    ("Request feedback", "Contact hiring manager for interview scorecard"),
    ("Follow up with client", "Share candidate update and confirm next step"),
    ("Schedule interview", "Coordinate panel availability and send invite"),
    ("Update status", "Update candidate stage and send status note"),
]

# Guaranteed bucket counts: 8 overdue (1 Rahul + 7 generated), 10 due_soon, 12 future, 10 completed = 40
BUCKETS = [
    ("overdue", 7, (-9, -1), "Pending"),
    ("due_soon", 10, (0, 1), "Pending"),
    ("future", 12, (2, 10), "Pending"),
    ("completed", 10, (-8, -1), "Completed"),
]


def seed():
    init_db()
    conn = get_db()
    cur = conn.cursor()

    # Reset tables in foreign-key-safe order so re-runs stay clean
    for table in ("stage_history", "actions", "applications", "candidates", "jobs", "recruiters"):
        cur.execute(f"DELETE FROM {table}")

    # 1. Recruiters (3)
    cur.executemany(
        "INSERT INTO recruiters (recruiter_id, name, email, role) VALUES (?, ?, ?, ?)",
        RECRUITERS,
    )

    # 2. Jobs (5)
    cur.executemany(
        """INSERT INTO jobs (job_id, job_title, company, priority, status, target_fill_date)
           VALUES (?, ?, ?, ?, ?, ?)""",
        JOBS,
    )
    job_priority_map = {j[0]: j[3] for j in JOBS}

    # 3. Candidates (30) — Candidate 1 is Rahul Sharma
    candidates = []
    for cid, name in enumerate(CANDIDATE_NAMES, start=1):
        email = name.lower().replace(" ", ".") + "@example.com"
        exp = 4 if cid == 1 else random.randint(1, 10)
        loc = "Bengaluru" if cid == 1 else random.choice(LOCATIONS)
        candidates.append((cid, name, email, exp, loc))

    cur.executemany(
        """INSERT INTO candidates (candidate_id, name, email, experience, location)
           VALUES (?, ?, ?, ?, ?)""",
        candidates,
    )

    # 4. Applications (35) — Application 1 is Rahul's 45/45 demo record
    # Exact stage mix across 35 applications:
    # Rahul = Interview (Pending feedback), plus 34 others across all 6 stages
    stage_pool = (
        ["Applied"] * 8
        + ["Shortlisted"] * 8
        + ["Interview"] * 8
        + ["Offer"] * 4
        + ["Hired"] * 3
        + ["Rejected"] * 3
    )
    random.shuffle(stage_pool)

    applications = []
    app_meta = {}  # app_id -> dict for consistent action & history generation
    used_pairs = set()

    # Hand-crafted Application 1: Rahul Sharma -> Python Developer (High), Interview, Pending feedback
    rahul_applied = TODAY - timedelta(days=12)
    rahul_last_act = TODAY - timedelta(days=5)  # Waiting 5 days -> +10
    applications.append((
        1, 1, 1, 1, "Interview",
        rahul_applied.isoformat(), rahul_last_act.isoformat(), "Pending",
    ))
    app_meta[1] = {
        "job_id": 1,
        "recruiter_id": 1,
        "stage": "Interview",
        "applied_at": rahul_applied,
        "last_activity_at": rahul_last_act,
        "feedback_status": "Pending",
    }
    used_pairs.add((1, 1))

    # Remaining 34 applications: first cover candidates 2..30, then 5 multi-role applications
    candidate_sequence = list(range(2, 31)) + random.sample(range(2, 31), 5)
    for idx, (cid, stage) in enumerate(zip(candidate_sequence, stage_pool), start=2):
        # Pick a job not already paired with this candidate
        available_jobs = [j[0] for j in JOBS if (cid, j[0]) not in used_pairs]
        jid = random.choice(available_jobs)
        used_pairs.add((cid, jid))

        rid = random.choice([1, 2, 3])
        applied_dt = TODAY - timedelta(days=random.randint(8, 28))
        last_act_dt = TODAY - timedelta(days=random.randint(0, 7))
        if last_act_dt < applied_dt:
            last_act_dt = applied_dt

        if stage == "Interview":
            feedback = random.choice(["Pending", "Pending", "Received"])
        elif stage in ("Offer", "Hired"):
            feedback = "Received"
        else:
            feedback = "None"

        applications.append((
            idx, cid, jid, rid, stage,
            applied_dt.isoformat(), last_act_dt.isoformat(), feedback,
        ))
        app_meta[idx] = {
            "job_id": jid,
            "recruiter_id": rid,
            "stage": stage,
            "applied_at": applied_dt,
            "last_activity_at": last_act_dt,
            "feedback_status": feedback,
        }

    cur.executemany(
        """INSERT INTO applications
           (application_id, candidate_id, job_id, recruiter_id, stage,
            applied_at, last_activity_at, feedback_status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        applications,
    )

    # 5. Stage History — full stage journey per application
    history_rows = []
    for app_id, meta in app_meta.items():
        stage = meta["stage"]
        if stage == "Rejected":
            path = ["Applied", "Shortlisted", "Rejected"]
        else:
            path = STAGE_ORDER[: STAGE_ORDER.index(stage) + 1]

        total_span = max((meta["last_activity_at"] - meta["applied_at"]).days, 0)
        steps = max(len(path) - 1, 1)
        prev_stage = None
        for step_idx, to_stage in enumerate(path):
            day_offset = int(round(total_span * (step_idx / steps)))
            changed_dt = meta["applied_at"] + timedelta(days=day_offset)
            history_rows.append((app_id, prev_stage, to_stage, changed_dt.isoformat()))
            prev_stage = to_stage

    cur.executemany(
        """INSERT INTO stage_history (application_id, from_stage, to_stage, changed_at)
           VALUES (?, ?, ?, ?)""",
        history_rows,
    )

    # 6. Actions (40)
    hired_app_ids = [aid for aid, m in app_meta.items() if m["stage"] == "Hired"]
    active_app_ids = [
        aid for aid, m in app_meta.items()
        if m["stage"] not in ("Hired", "Rejected") and aid != 1
    ]
    all_non_rahul_ids = [aid for aid in app_meta if aid != 1]

    actions = []
    action_id = 1

    # Hand-crafted Action 1: Rahul's 45/45 High-priority overdue action
    rahul_due = TODAY - timedelta(days=5)  # 5 days overdue -> +15
    rahul_created = rahul_due - timedelta(days=4)
    rahul_score, _, _ = score_action(
        rahul_due,
        app_meta[1]["last_activity_at"],
        job_priority_map[1],
        app_meta[1]["feedback_status"],
        today=TODAY,
    )
    actions.append((
        action_id, 1, "Request feedback",
        "Follow up with FinEdge Labs hiring manager on Rahul Sharma's technical interview",
        rahul_created.isoformat(), rahul_due.isoformat(),
        "Pending", rahul_score, app_meta[1]["recruiter_id"], None,
    ))
    action_id += 1

    # Generate remaining 39 actions by bucket
    for bucket_name, count, (lo, hi), status in BUCKETS:
        if bucket_name == "completed":
            # Guarantee every Hired application gets a Completed action
            chosen_apps = list(hired_app_ids) + [
                random.choice(all_non_rahul_ids) for _ in range(count - len(hired_app_ids))
            ]
        else:
            # Active pipeline applications only (Hired/Rejected never get Pending actions)
            chosen_apps = [random.choice(active_app_ids) for _ in range(count)]

        for app_id in chosen_apps:
            meta = app_meta[app_id]
            action_type, desc = random.choice(ACTION_TEMPLATES)
            due_dt = TODAY + timedelta(days=random.randint(lo, hi))
            created_dt = due_dt - timedelta(days=random.randint(3, 10))
            completed_dt = (
                (due_dt + timedelta(days=random.randint(-1, 1))).isoformat()
                if status == "Completed"
                else None
            )

            score, _, _ = score_action(
                due_dt,
                meta["last_activity_at"],
                job_priority_map[meta["job_id"]],
                meta["feedback_status"],
                today=TODAY,
            )

            actions.append((
                action_id, app_id, action_type, desc,
                created_dt.isoformat(), due_dt.isoformat(),
                status, score, meta["recruiter_id"], completed_dt,
            ))
            action_id += 1

    cur.executemany(
        """INSERT INTO actions
           (action_id, application_id, action_type, description, created_at,
            due_at, status, priority_score, assigned_recruiter_id, completed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        actions,
    )

    conn.commit()
    conn.close()
    print(f"Seeded HirePulse DB (ref date: {TODAY.isoformat()}) — Rahul score: {rahul_score}/45")


if __name__ == "__main__":
    seed()