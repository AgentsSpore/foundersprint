from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from models import (
    CheckinResponse, FounderCreate, FounderResponse,
    MilestoneCreate, MilestoneResponse,
)
from tracker import (
    init_db, create_founder, list_founders, get_founder,
    create_milestone, list_milestones, run_checkin,
)

DB_PATH = "foundersprint.db"


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db = await init_db(DB_PATH)
    yield
    await app.state.db.close()


app = FastAPI(
    title="FoundersPrint",
    description="Startup accountability engine — track milestones, detect drift, get coaching",
    version="0.1.0",
    lifespan=lifespan,
)


@app.post("/founders", response_model=FounderResponse)
async def register_founder(body: FounderCreate):
    return await create_founder(app.state.db, body.name, body.github_username, body.project_name, body.goal)


@app.get("/founders", response_model=list[FounderResponse])
async def index_founders():
    return await list_founders(app.state.db)


@app.get("/founders/{founder_id}", response_model=FounderResponse)
async def show_founder(founder_id: int):
    f = await get_founder(app.state.db, founder_id)
    if not f:
        raise HTTPException(404, "Founder not found")
    return f


@app.post("/founders/{founder_id}/milestones", response_model=MilestoneResponse)
async def add_milestone(founder_id: int, body: MilestoneCreate):
    f = await get_founder(app.state.db, founder_id)
    if not f:
        raise HTTPException(404, "Founder not found")
    return await create_milestone(app.state.db, founder_id, body.title, body.due_date, body.commit_target)


@app.get("/founders/{founder_id}/milestones", response_model=list[MilestoneResponse])
async def show_milestones(founder_id: int):
    return await list_milestones(app.state.db, founder_id)


@app.post("/founders/{founder_id}/checkin", response_model=CheckinResponse)
async def weekly_checkin(founder_id: int):
    f = await get_founder(app.state.db, founder_id)
    if not f:
        raise HTTPException(404, "Founder not found")
    return await run_checkin(app.state.db, founder_id)
