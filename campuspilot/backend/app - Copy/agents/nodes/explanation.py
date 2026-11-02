import time

from google import genai

from app.core.config import settings
from app.db.memory_store import store
from app.utils.token_tracker import tracker


def explain_changes(state):
    # Write a short explanation of why the plan changed
    facts = []
    for topic in state["weak_topics"]:
        facts.append(f"- {topic['topic']}: {', '.join(topic['reasons'])}")
    for item in state.get("material", [])[:4]:
        facts.append(f"- Review {item['topic']} in {item['source']}, page {item['page']}")
    for warning in state.get("warnings", []):
        facts.append(f"- Warning: {warning}")

    facts_text = "\n".join(facts)

    # Plain text used if Gemini is unavailable
    fallback = (
        "Your plan was revised because these topics need attention:\n"
        f"{facts_text}\n"
        "They now have top priority in your schedule."
    )

    explanation = fallback
    if settings.gemini_api_key:
        try:
            client = genai.Client(api_key=settings.gemini_api_key)
            start = time.time()
            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=(
                    "Explain to a university student, in 3 to 4 friendly sentences, "
                    "why their study plan was changed. Use only these facts:\n"
                    f"{facts_text}"
                ),
            )
            usage = response.usage_metadata
            tracker.record(
                "explanation",
                getattr(usage, "prompt_token_count", 0) or 0,
                getattr(usage, "candidates_token_count", 0) or 0,
                time.time() - start,
            )
            explanation = response.text or fallback
        except Exception as error:
            # Show the problem in the server terminal instead of hiding it
            print(f"[explanation] Gemini call failed, using fallback text: {error}")
            explanation = fallback

    store.update_revision(state["revision_id"], explanation=explanation)
    return {"explanation": explanation}