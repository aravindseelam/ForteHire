import os
import sqlite3

DB = os.path.join("database", "hirepulse.db")

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

SCHEMA = """
CREATE TABLE IF NOT EXISTS recruiters (
    recruiter_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    role TEXT DEFAULT 'Recruiter'
);

CREATE TABLE IF NOT EXISTS jobs (
    job_id INTEGER PRIMARY KEY,
    job_title TEXT NOT NULL,
    company TEXT NOT NULL,
    priority TEXT NOT NULL CHECK(priority IN ('Low','Normal','High','Critical')),
    status TEXT NOT NULL DEFAULT 'Open' CHECK(status IN ('Open','Paused','Closed')),
    target_fill_date TEXT
);

CREATE TABLE IF NOT EXISTS candidates (
    candidate_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    experience INTEGER,
    location TEXT
);

CREATE TABLE IF NOT EXISTS applications (
    application_id INTEGER PRIMARY KEY,
    candidate_id INTEGER NOT NULL REFERENCES candidates(candidate_id),
    job_id INTEGER NOT NULL REFERENCES jobs(job_id),
    recruiter_id INTEGER NOT NULL REFERENCES recruiters(recruiter_id),
    stage TEXT NOT NULL CHECK(stage IN
        ('Applied','Shortlisted','Interview','Offer','Hired','Rejected')),
    applied_at TEXT NOT NULL,
    last_activity_at TEXT NOT NULL,
    feedback_status TEXT NOT NULL DEFAULT 'None'
        CHECK(feedback_status IN ('None','Pending','Received'))
);

CREATE TABLE IF NOT EXISTS actions (
    action_id INTEGER PRIMARY KEY,
    application_id INTEGER NOT NULL REFERENCES applications(application_id),
    action_type TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL,
    due_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Pending'
        CHECK(status IN ('Pending','Snoozed','Completed')),
    snoozed_until TEXT,
    snooze_count INTEGER NOT NULL DEFAULT 0,
    priority_score INTEGER DEFAULT 0,
    assigned_recruiter_id INTEGER NOT NULL REFERENCES recruiters(recruiter_id),
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS stage_history (
    id INTEGER PRIMARY KEY,
    application_id INTEGER NOT NULL REFERENCES applications(application_id),
    from_stage TEXT,
    to_stage TEXT NOT NULL,
    changed_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_actions_queue
    ON actions(assigned_recruiter_id, status, due_at);
CREATE INDEX IF NOT EXISTS idx_applications_stage
    ON applications(stage);
CREATE INDEX IF NOT EXISTS idx_stage_history_app
    ON stage_history(application_id, changed_at);
"""

def init_db():
    os.makedirs("database", exist_ok=True)
    conn = get_db()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print(f"Initialized database at {DB}")