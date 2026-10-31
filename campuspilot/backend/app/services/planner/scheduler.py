from datetime import date, timedelta


class StudyPlanner:
    """Builds a day-by-day study schedule from exam dates and topics."""

    def __init__(self, max_hours_per_topic_per_day=2.0):
        # Stops one topic from taking the whole day (keeps variety)
        self.max_per_topic = max_hours_per_topic_per_day

    def generate(self, courses, daily_hours, start_date):
        # 1. Flatten all topics into one list, remembering each exam date
        topics = []
        for course in courses:
            for topic in course["topics"]:
                topics.append({
                    "course_id": course.get("id"),
                    "topic_id": topic.get("id"),
                    "course": course["name"],
                    "topic": topic["name"],
                    "priority": topic["priority"],        # 3 = high, 1 = low
                    "remaining": topic["hours"],
                    "exam_date": course["exam_date"],
                })

        # 2. Earliest exam first, then highest priority first
        topics.sort(key=lambda t: (t["exam_date"], -t["priority"]))

        # 3. Walk through the days and fill each one
        tasks = []
        last_exam = max(t["exam_date"] for t in topics)
        day = start_date

        while day < last_exam:
            hours_left = daily_hours

            for t in topics:
                if hours_left <= 0:
                    break
                # Only study a topic before its exam day
                if t["remaining"] <= 0 or day >= t["exam_date"]:
                    continue

                hours = min(t["remaining"], hours_left, self.max_per_topic)
                tasks.append({
                    "date": day,
                    "course_id": t["course_id"],
                    "topic_id": t["topic_id"],
                    "course": t["course"],
                    "topic": t["topic"],
                    "hours": hours,
                })
                t["remaining"] -= hours
                hours_left -= hours

            day += timedelta(days=1)

        # 4. Anything left over did not fit before its exam
        warnings = []
        for t in topics:
            if t["remaining"] > 0:
                warnings.append(
                    f"Not enough time: {t['remaining']} hour(s) of "
                    f"'{t['topic']}' ({t['course']}) could not be scheduled "
                    f"before the exam on {t['exam_date']}."
                )

        return tasks, warnings