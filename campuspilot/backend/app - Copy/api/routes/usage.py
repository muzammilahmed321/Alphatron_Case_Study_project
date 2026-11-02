from fastapi import APIRouter

from app.db.memory_store import store
from app.utils.token_tracker import tracker

router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("")
def get_usage():
    return tracker.summary()


@router.get("/calls")
def get_calls():
    return tracker.calls


@router.post("/reset")
def reset_usage():
    tracker.reset()
    return {"message": "Usage log cleared"}


@router.post("/reset-all-data")
def reset_all_data():
    #Testing helper: clears the usage log AND all courses, topics, tasks, and quizzes.
    tracker.reset()
    store.reset()
    return {"message": "All data cleared"}