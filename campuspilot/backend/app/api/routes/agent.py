import uuid
from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException
from langgraph.types import Command
from pydantic import BaseModel

from app.agents.graph import graph
from app.db.memory_store import store

router = APIRouter(prefix="/agent", tags=["agent"])


class RunRequest(BaseModel):
    daily_hours: float
    today: Optional[date] = None    # set a date to test missed tasks


class Decision(BaseModel):
    approve: bool


def build_response(thread_id):
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = graph.get_state(config)
    values = snapshot.values

    # snapshot.next is not empty while the agent is paused
    if snapshot.next:
        revision = store.get_revision(values["revision_id"])
        return {
            "status": "waiting_for_approval",
            "thread_id": thread_id,
            "explanation": revision["explanation"],
            "weak_topics": [t["topic"] for t in values["weak_topics"]],
            "warnings": values.get("warnings", []),
            "problems": values.get("problems", []),
            "review_material": values.get("material", []),
            "proposed_tasks": revision["proposed_tasks"],
        }

    return {
        "status": "finished",
        "thread_id": thread_id,
        "route": values.get("route"),
        "message": values.get("message"),
    }


@router.post("/run")
def run_agent(body: RunRequest):
    if body.daily_hours <= 0:
        raise HTTPException(status_code=400, detail="daily_hours must be above 0")

    thread_id = uuid.uuid4().hex[:8]
    config = {"configurable": {"thread_id": thread_id}}
    start = {
        "daily_hours": body.daily_hours,
        "today": (body.today or date.today()).isoformat(),
    }
    try:
        graph.invoke(start, config)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Agent error: {error}")
    return build_response(thread_id)


@router.post("/{thread_id}/decision")
def decide(thread_id: str, body: Decision):
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = graph.get_state(config)
    if not snapshot.next:
        raise HTTPException(status_code=400, detail="Nothing is waiting for approval")

    decision = "approve" if body.approve else "reject"
    graph.invoke(Command(resume=decision), config)
    return build_response(thread_id)