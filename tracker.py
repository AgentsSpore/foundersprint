from __future__ import annotations

import json
import random
from datetime import datetime, timezone

import aiosqlite

SQL_TABLES = """
CREATE TABLE IF NOT EXISTS founders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    github_username TEXT NOT NULL,
    project_name TEXT NOT NULL,
    goal TEXT NOT NULL,
    drift_level TEXT NOT NULL DEFAULT 'on_track',
    total_commits INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS milestones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    founder_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    due_date TEXT NOT NULL,
    commit_target INTEGER NOT NULL DEFAULT 5,
    current_commits INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    FOREIGN KEY (founder_id) REFERENCES founders(id)
);
"""


async def init_db(path: str) -> aiosqlite.Connection:
    db = await aiosqlite.connect(path)
    db.row_factory = aiosqlite.Row
    await db.executescript(SQL_TABLES)
    await db.commit()
    return db


async def create_founder(db: aiosqlite.Connection, name: str, github_username: str, project_name: str, goal: str) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    cur = await db.execute(
        "INSERT INTO founders (name, github_username, project_name, goal, created_at) VALUES (?, ?, ?, ?, ?)",
        (name, github_username, project_name, goal, now),
    )
    await db.commit()
    rows = await db.execute_fetchall("SELECT * FROM founders WHERE id = ?", (cur.lastrowid,))
    return dict(rows[0])


async def list_founders(db: aiosqlite.Connection) -> list[dict]:
    rows = await db.execute_fetchall("SELECT * FROM founders ORDER BY created_at DESC")
    return [dict(r) for r in rows]


async def get_founder(db: aiosqlite.Connection, founder_id: int) -> dict | None:
    rows = await db.execute_fetchall("SELECT * FROM founders WHERE id = ?", (founder_id,))
    return dict(rows[0]) if rows else None


async def create_milestone(db: aiosqlite.Connection, founder_id: int, title: str, due_date: str, commit_target: int) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    cur = await db.execute(
        "INSERT INTO milestones (founder_id, title, due_date, commit_target, created_at) VALUES (?, ?, ?, ?, ?)",
        (founder_id, title, due_date, commit_target, now),
    )
    await db.commit()
    rows = await db.execute_fetchall("SELECT * FROM milestones WHERE id = ?", (cur.lastrowid,))
    return dict(rows[0])


async def list_milestones(db: aiosqlite.Connection, founder_id: int) -> list[dict]:
    rows = await db.execute_fetchall(
        "SELECT * FROM milestones WHERE founder_id = ? ORDER BY due_date", (founder_id,)
    )
    return [dict(r) for r in rows]


async def run_checkin(db: aiosqlite.Connection, founder_id: int) -> dict:
    """Simulate a weekly check-in: fetch GitHub commits (mocked), update milestones, detect drift."""
    founder = await get_founder(db, founder_id)
    if not founder:
        raise ValueError("Founder not found")

    milestones = await list_milestones(db, founder_id)
    now = datetime.now(timezone.utc)

    # Simulate GitHub commit count (in real MVP would call GitHub API)
    simulated_commits = random.randint(0, 15)
    total = founder["total_commits"] + simulated_commits

    on_track = 0
    overdue = 0

    for ms in milestones:
        if ms["status"] == "completed":
            on_track += 1
            continue

        new_commits = ms["current_commits"] + simulated_commits
        due = datetime.fromisoformat(ms["due_date"].replace("Z", "+00:00")) if "T" in ms["due_date"] else datetime.fromisoformat(ms["due_date"] + "T23:59:59+00:00")

        if new_commits >= ms["commit_target"]:
            await db.execute("UPDATE milestones SET status = 'completed', current_commits = ? WHERE id = ?", (new_commits, ms["id"]))
            on_track += 1
        elif now > due:
            await db.execute("UPDATE milestones SET status = 'overdue', current_commits = ? WHERE id = ?", (new_commits, ms["id"]))
            overdue += 1
        else:
            await db.execute("UPDATE milestones SET current_commits = ? WHERE id = ?", (new_commits, ms["id"]))
            on_track += 1

    # Calculate drift level
    if not milestones:
        drift = "on_track"
    elif overdue == 0 and simulated_commits >= 5:
        drift = "on_track"
    elif overdue == 0 and simulated_commits >= 1:
        drift = "slight_drift"
    elif overdue >= 1 and simulated_commits >= 1:
        drift = "major_drift"
    else:
        drift = "stalled"

    # Generate coaching message
    messages = {
        "on_track": f"Great progress, {founder['name']}! {simulated_commits} commits this week. Keep shipping!",
        "slight_drift": f"Hey {founder['name']}, only {simulated_commits} commits this week. Your milestone deadlines are approaching — time to focus.",
        "major_drift": f"{founder['name']}, you have {overdue} overdue milestone(s) and only {simulated_commits} commits. Let's talk about what's blocking you.",
        "stalled": f"{founder['name']}, zero commits detected. Are you stuck? Pivoting? Let's schedule a call to realign.",
    }

    await db.execute(
        "UPDATE founders SET drift_level = ?, total_commits = ? WHERE id = ?",
        (drift, total, founder_id),
    )
    await db.commit()

    return {
        "founder_id": founder_id,
        "founder_name": founder["name"],
        "drift_level": drift,
        "milestones_on_track": on_track,
        "milestones_overdue": overdue,
        "simulated_commits": simulated_commits,
        "message": messages[drift],
    }
