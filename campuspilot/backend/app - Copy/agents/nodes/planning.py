from datetime import date

from app.db.memory_store import store
from app.services.planner.scheduler import StudyPlanner
from app.services.planner.validator import PlanValidator

planner = StudyPlanner()
validator = PlanValidator()

EXTRA_HOURS = 1.0   # extra hours per weak topic on the first try


def build_revision(state):
    # Build a new plan: weak topics get top priority and extra hours
    attempt = state.get("attempt", 0) + 1
    today = date.fromisoformat(state["today"])

    # On a retry, skip the extra hours (they probably did not fit)
    extra = EXTRA_HOURS if attempt == 1 else 0.0
    weak_ids = {t["topic_id"] for t in state["weak_topics"]}
    adjustments = [{"topic_id": tid, "extra_hours": extra} for tid in weak_ids]

    courses = []
    for course in store.list_courses():
        if course["exam_date"] <= today:
            continue    # exam already passed

        topics = []
        done_tasks = store.list_tasks(status="done", course_id=course["id"])
        for topic in store.list_topics(course["id"]):
            hours_done = sum(t["hours"] for t in done_tasks if t["topic_id"] == topic["id"])
            hours = topic["hours"] - hours_done
            priority = topic["priority"]

            if topic["id"] in weak_ids:
                hours += extra
                priority = 3

            if hours > 0:
                topics.append({**topic, "hours": hours, "priority": priority})

        if topics:
            courses.append({**course, "topics": topics})

    if courses:
        tasks, warnings = planner.generate(courses, state["daily_hours"], today)
    else:
        tasks, warnings = [], ["No upcoming exams with remaining study hours."]

    # Create the proposal the first time, update it on retries
    weak_names = [t["topic"] for t in state["weak_topics"]]
    if state.get("revision_id"):
        store.update_revision(state["revision_id"], proposed_tasks=tasks)
        revision_id = state["revision_id"]
    else:
        revision_id = store.add_revision(tasks, "", weak_names)["id"]

    return {
        "attempt": attempt,
        "revision_id": revision_id,
        "adjustments": adjustments,
        "warnings": warnings,
    }


def validate_plan(state):
    # Check the proposed plan with code
    revision = store.get_revision(state["revision_id"])
    problems = validator.check(
        revision["proposed_tasks"],
        store.list_courses(),
        state["daily_hours"],
    )
    return {"problems": problems}