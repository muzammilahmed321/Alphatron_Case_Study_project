from typing import TypedDict


class AgentState(TypedDict, total=False):
    # Inputs
    daily_hours: float
    today: str

    # Routing
    route: str

    # Analysis
    report: list
    weak_topics: list
    material: list

    # Planning
    adjustments: list
    attempt: int
    revision_id: str
    warnings: list
    problems: list

    # Review and result
    explanation: str
    decision: str
    message: str