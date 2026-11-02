from app.db.memory_store import store


def persist(state):
    # Save the plan if approved, otherwise keep the old one
    revision_id = state["revision_id"]

    if state.get("decision") == "approve":
        store.approve_revision(revision_id)
        for item in state.get("adjustments", []):
            topic = store.get_topic(item["topic_id"])
            if topic:
                store.update_topic(
                    item["topic_id"],
                    priority=3,
                    hours=topic["hours"] + item["extra_hours"],
                )
        return {"message": "Plan approved and saved."}

    store.reject_revision(revision_id)
    return {"message": "Plan rejected. Your current plan is unchanged."}