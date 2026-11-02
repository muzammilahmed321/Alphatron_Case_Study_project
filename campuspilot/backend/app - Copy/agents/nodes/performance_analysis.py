from app.db.memory_store import store
from app.services.progress.analyzer import ProgressAnalyzer

analyzer = ProgressAnalyzer()


def analyze_performance(state):
    # Check quiz results and missed tasks, then pick a route
    report = analyzer.analyze(
        store.list_all_topics(),
        store.list_quiz_results(),
        store.list_tasks(),
    )

    weak = [r for r in report if r["status"] == "weak"]
    untested = [r for r in report if r["status"] == "untested"]

    if weak:
        route = "revise"
    elif untested:
        route = "practice"
    else:
        route = "on_track"

    return {"report": report, "weak_topics": weak, "route": route}