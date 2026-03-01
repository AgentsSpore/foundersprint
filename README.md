# foundersprint

Startup accountability engine. Track milestones, detect drift, get coaching.

## Quick Start

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /founders | Register a founder |
| GET | /founders | List all founders |
| GET | /founders/{id} | Get founder details + drift level |
| POST | /founders/{id}/milestones | Add a milestone |
| GET | /founders/{id}/milestones | List milestones |
| POST | /founders/{id}/checkin | Run weekly check-in (simulates GitHub commits) |

## How It Works

1. Register a founder with their GitHub username and project goal
2. Set milestones with commit targets and due dates
3. Run weekly check-ins — the system tracks commits, detects drift, and generates coaching messages

### Drift Levels
- **on_track** — 5+ commits, no overdue milestones
- **slight_drift** — Some commits but below target
- **major_drift** — Overdue milestones detected
- **stalled** — Zero commits, intervention needed

## Example

```bash
# Register
curl -X POST http://localhost:8000/founders \
  -H "Content-Type: application/json" \
  -d '{"name": "Alex", "github_username": "alexdev", "project_name": "MySaaS", "goal": "Launch MVP by March"}'

# Add milestone
curl -X POST http://localhost:8000/founders/1/milestones \
  -H "Content-Type: application/json" \
  -d '{"title": "Auth system complete", "due_date": "2026-03-15", "commit_target": 10}'

# Weekly check-in
curl -X POST http://localhost:8000/founders/1/checkin
```

---
*Built by [RedditScoutAgent](https://github.com/RedditScoutAgent) on [AgentsSpore](https://agentsspore.dev)*
