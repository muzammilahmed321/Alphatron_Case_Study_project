from app.api.routes.documents import retriever


def retrieve_material(state):
    # Find PDF pages about each weak topic
    material = []
    for topic in state["weak_topics"]:
        for chunk in retriever.search(topic["topic"], top_k=2):
            material.append({
                "topic": topic["topic"],
                "source": chunk["source"],
                "page": chunk["page"],
            })
    return {"material": material}