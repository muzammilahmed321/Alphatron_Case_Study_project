class PlanValidator:
    """Double-checks a schedule so we never trust it blindly."""

    def check(self, tasks, courses, daily_hours):
        problems = []

        exam_dates = {c["name"]: c["exam_date"] for c in courses}

        # 1: no day goes over the daily limit
        hours_per_day = {}
        for task in tasks:
            hours_per_day[task["date"]] = hours_per_day.get(task["date"], 0) + task["hours"]
        for day, total in hours_per_day.items():
            if total > daily_hours + 0.001:
                problems.append(f"{day} has {total} hours, over the limit of {daily_hours}")

        #2: nothing is scheduled on or after its exam day
        for task in tasks:
            if task["date"] >= exam_dates[task["course"]]:
                problems.append(f"'{task['topic']}' is scheduled on or after its exam")

        return problems