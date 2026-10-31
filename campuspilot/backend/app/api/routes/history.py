from fastapi import APIRouter

from app.db.memory_store import store

router = APIRouter(prefix="/history", tags=["history"])


@router.get("")
def get_history():
    # Group quiz answers by quiz
    by_quiz = {}
    for result in store.list_quiz_results():
        by_quiz.setdefault(result["quiz_id"], []).append(result)

    quizzes = []
    for quiz_id, results in by_quiz.items():
        quiz = store.get_quiz(quiz_id)
        topic = store.get_topic(quiz["topic_id"]) if quiz else None
        correct = sum(1 for r in results if r["correct"])
        quizzes.append({
            "quiz_id": quiz_id,
            "topic": topic["name"] if topic else "(deleted topic)",
            "score": f"{correct}/{len(results)}",
            "accuracy": round(correct / len(results), 2),
            "time": results[0]["time"],
        })
    quizzes.sort(key=lambda q: q["time"], reverse=True)

    revisions = [
        {
            "id": r["id"],
            "status": r["status"],
            "explanation": r["explanation"],
            "weak_topics": r["weak_topics"],
            "task_count": len(r["proposed_tasks"]),
            "time": r["created_at"],
        }
        for r in store.list_revisions()
    ]
    revisions.sort(key=lambda r: r["time"], reverse=True)

    finished = store.list_tasks(status="done") + store.list_tasks(status="missed")
    finished.sort(key=lambda t: t["date"], reverse=True)

    return {"quizzes": quizzes, "revisions": revisions, "tasks": finished}