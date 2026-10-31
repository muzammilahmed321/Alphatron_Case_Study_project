class ProgressAnalyzer:
    #Finds weak topics from quiz results and missed tasks.

    def __init__(self, weak_accuracy=0.6, min_questions=2, missed_limit=2):
        self.weak_accuracy = weak_accuracy    
        self.min_questions = min_questions    
        self.missed_limit = missed_limit      

    def analyze(self, topics, quiz_results, tasks):
        report = []

        for topic in topics:
            results = [r for r in quiz_results if r["topic_id"] == topic["id"]]
            answered = len(results)
            correct = sum(1 for r in results if r["correct"])
            accuracy = round(correct / answered, 2) if answered else None

            missed = sum(
                1 for t in tasks
                if t["topic_id"] == topic["id"] and t["status"] == "missed"
            )

            # Decide the status and say why
            reasons = []
            if answered >= self.min_questions and accuracy < self.weak_accuracy:
                reasons.append(f"quiz accuracy is {int(accuracy * 100)}%")
            if missed >= self.missed_limit:
                reasons.append(f"{missed} study tasks were missed")

            if reasons:
                status = "weak"
            elif answered < self.min_questions:
                status = "untested"
            else:
                status = "on_track"

            report.append({
                "topic_id": topic["id"],
                "topic": topic["name"],
                "course_id": topic["course_id"],
                "questions_answered": answered,
                "accuracy": accuracy,
                "missed_tasks": missed,
                "status": status,
                "reasons": reasons,
            })

        # Weak topics first, then untested, then on track
        order = {"weak": 0, "untested": 1, "on_track": 2}
        report.sort(key=lambda r: order[r["status"]])
        return report