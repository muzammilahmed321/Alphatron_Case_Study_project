from fastapi import APIRouter

from app.db.memory_store import store
from app.services.progress.analyzer import ProgressAnalyzer

router = APIRouter(prefix="/progress", tags=["progress"])

analyzer = ProgressAnalyzer()


@router.get("/topics")
def topic_progress():
    return analyzer.analyze(
        store.list_all_topics(),
        store.list_quiz_results(),
        store.list_tasks(),
    )


@router.get("/weak-topics")
def weak_topics():
    report = analyzer.analyze(
        store.list_all_topics(),
        store.list_quiz_results(),
        store.list_tasks(),
    )
    weak = [r for r in report if r["status"] == "weak"]
    return {"weak_count": len(weak), "weak_topics": weak}