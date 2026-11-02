from langgraph.graph import END


def route_after_load(state):
    return END if state["route"] == "no_data" else "analyze_performance"


def route_after_analysis(state):
    return state["route"]    # "revise", "practice", or "on_track"


def route_after_validation(state):
    has_trouble = state.get("problems") or state.get("warnings")
    if has_trouble and state.get("attempt", 0) < 2:
        return "retry"       # rebuild a safer plan
    return "explain"


def recommend_practice(state):
    names = [r["topic"] for r in state["report"] if r["status"] == "untested"]
    return {"message": "Take a practice quiz on: " + ", ".join(names)}


def on_track(state):
    return {"message": "You are on track. No changes needed."}