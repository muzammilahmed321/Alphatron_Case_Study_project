class SavedPlanRequest(BaseModel):
    daily_hours: float
    start_date: Optional[date] = None


@router.post("/generate-and-save")
def generate_and_save(body: SavedPlanRequest):
    if body.daily_hours <= 0:
        raise HTTPException(status_code=400, detail="daily_hours must be above 0")

    start = body.start_date or date.today()

    # Build the course list from what is saved in the store
    courses = []
    for c in store.list_courses():
        topics = store.list_topics(c["id"])
        if topics:
            courses.append({**c, "topics": topics})

    if not courses:
        raise HTTPException(status_code=400, detail="Add courses with topics first")

    tasks, warnings = planner.generate(courses, body.daily_hours, start)
    problems = validator.check(tasks, courses, body.daily_hours)

    # Only save if the plan is valid
    if problems:
        raise HTTPException(status_code=500, detail=f"Invalid plan: {problems}")

    saved = store.save_plan(tasks)
    return {
        "saved_tasks": len(saved),
        "warnings": warnings,
        "tasks": saved,
    }