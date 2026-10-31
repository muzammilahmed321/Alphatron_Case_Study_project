from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db.memory_store import store

router = APIRouter(prefix="/tasks", tags=["tasks"])

VALID_STATUSES = ("pending", "done", "missed")


class StatusUpdate(BaseModel):
    status: str   # pending, done, or missed


@router.get("")
def list_tasks(status: Optional[str] = None, course_id: Optional[str] = None):
    return store.list_tasks(status, course_id)


@router.get("/summary")
def summary():
    return store.get_plan_summary()


@router.post("/check-missed")
def check_missed(today: Optional[date] = None):
    """Mark pending tasks from past days as missed."""
    today = today or date.today()
    newly_missed = []
    for task in store.list_tasks(status="pending"):
        if task["date"] < today:
            store.set_task_status(task["id"], "missed")
            newly_missed.append(task)
    return {"marked_missed": len(newly_missed), "tasks": newly_missed}


@router.patch("/{task_id}")
def update_task(task_id: str, body: StatusUpdate):
    if body.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"status must be one of {VALID_STATUSES}")
    task = store.set_task_status(task_id, body.status)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete("/{task_id}")
def delete_task(task_id: str):
    if not store.delete_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted"}