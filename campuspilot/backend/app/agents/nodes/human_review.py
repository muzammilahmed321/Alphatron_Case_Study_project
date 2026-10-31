from langgraph.types import interrupt


def human_review(state):
    # Pause here until the student approves or rejects
    decision = interrupt({
        "revision_id": state["revision_id"],
        "question": "Approve the revised study plan?",
    })
    return {"decision": decision}