from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db.memory_store import store
from app.services.planner.scheduler import StudyPlanner
from app.services.planner.validator import PlanValidator

router = APIRouter(prefix="/plans", tags=["plans"])

planner = StudyPlanner()
validator = PlanValidator()


class Topic(BaseModel):
    name: str
    priority: int = 2      # 1 = low, 2 = medium, 3 = high
    hours: float           # estimated study hours needed


class Course(BaseModel):
    name: str
    exam_date: date
    topics: list[Topic]


class PlanRequest(BaseModel):
    courses: list[Course]
    daily_hours: float
    start_date: Optional[date] = None   # defaults to today


class SavedPlanRequest(BaseModel):
    daily_hours: float
    start_date: Optional[date] = None


@router.post("/generate")
def generate_plan(body: PlanRequest):
    if body.daily_hours <= 0:
        raise HTTPException(status_code=400, detail="daily_hours must be above 0")
    if not any(c.topics for c in body.courses):
        raise HTTPException(status_code=400, detail="Add at least one topic")

    start = body.start_date or date.today()
    courses = [c.model_dump() for c in body.courses]

    if all(c["exam_date"] <= start for c in courses):
        raise HTTPException(status_code=400, detail="All exam dates are in the past")

    tasks, warnings = planner.generate(courses, body.daily_hours, start)
    problems = validator.check(tasks, courses, body.daily_hours)

    return {
        "total_hours_scheduled": sum(t["hours"] for t in tasks),
        "tasks": tasks,
        "warnings": warnings,
        "validation_problems": problems,
    }


@router.post("/generate-and-save")
def generate_and_save(body: SavedPlanRequest):
    if body.daily_hours <= 0:
        raise HTTPException(status_code=400, detail="daily_hours must be above 0")

    start = body.start_date or date.today()

    # Build the course list from what is saved in the store
    courses = []
    for c in store.list_courses():
        topics = store.list_topics(c["id"])
        if topics:
            courses.append({**c, "topics": topics})

    if not courses:
        raise HTTPException(status_code=400, detail="Add courses with topics first")

    tasks, warnings = planner.generate(courses, body.daily_hours, start)
    problems = validator.check(tasks, courses, body.daily_hours)

    # Only save if the plan is valid
    if problems:
        raise HTTPException(status_code=500, detail=f"Invalid plan: {problems}")

    saved = store.save_plan(tasks)
    return {
        "saved_tasks": len(saved),
        "warnings": warnings,
        "tasks": saved,
    }