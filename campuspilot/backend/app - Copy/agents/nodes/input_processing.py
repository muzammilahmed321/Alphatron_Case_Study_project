from datetime import date

from app.db.memory_store import store


def load_context(state):
    # Read saved data and mark overdue pending tasks as missed
    today = state.get("today") or date.today().isoformat()
    today_date = date.fromisoformat(today)

    for task in store.list_tasks(status="pending"):
        if task["date"] < today_date:
            store.set_task_status(task["id"], "missed")

    if not store.list_all_topics():
        return {
            "today": today,
            "route": "no_data",
            "message": "No courses or topics found. Add them first.",
        }

    return {"today": today, "route": "ok", "attempt": 0}