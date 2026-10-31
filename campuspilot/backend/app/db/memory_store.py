import uuid
from datetime import datetime


class MemoryStore:
    """Keeps all app data in memory."""

    def __init__(self):
        self.courses = {}        # course_id -> course dict
        self.topics = {}         # topic_id -> topic dict
        self.tasks = {}          # task_id -> task dict
        self.quizzes = {}        # quiz_id -> quiz dict
        self.quiz_results = []   # list of graded answers
        self.revisions = {}      # revision_id -> proposed plan change

    def _new_id(self):
        return uuid.uuid4().hex[:8]

    def _now(self):
        return datetime.now().isoformat(timespec="seconds")

    def reset(self):
        """Delete all data. Handy for starting a fresh test."""
        self.__init__()

   
    # Courses
   
    def add_course(self, name, exam_date):
        course_id = self._new_id()
        self.courses[course_id] = {
            "id": course_id,
            "name": name,
            "exam_date": exam_date,
        }
        return self.courses[course_id]

    def get_course(self, course_id):
        return self.courses.get(course_id)

    def list_courses(self):
        return list(self.courses.values())

    def update_course(self, course_id, name=None, exam_date=None):
        course = self.courses.get(course_id)
        if not course:
            return None
        if name is not None:
            course["name"] = name
        if exam_date is not None:
            course["exam_date"] = exam_date
        return course

    def delete_course(self, course_id):
        #Delete a course and everything that belongs to it.
        if course_id not in self.courses:
            return False
        for topic in self.list_topics(course_id):
            self._remove_topic_data(topic["id"])
        self.tasks = {
            tid: t for tid, t in self.tasks.items() if t["course_id"] != course_id
        }
        del self.courses[course_id]
        return True

   
    # Topics
  
    def add_topic(self, course_id, name, priority, hours):
        topic_id = self._new_id()
        self.topics[topic_id] = {
            "id": topic_id,
            "course_id": course_id,
            "name": name,
            "priority": priority,   # 1 = low, 3 = high
            "hours": hours,         # estimated study hours
        }
        return self.topics[topic_id]

    def get_topic(self, topic_id):
        return self.topics.get(topic_id)

    def list_topics(self, course_id):
        return [t for t in self.topics.values() if t["course_id"] == course_id]

    def list_all_topics(self):
        return list(self.topics.values())

    def update_topic(self, topic_id, priority=None, hours=None, name=None):
        """Change a topic (the recovery agent and the edit form use this)."""
        topic = self.topics.get(topic_id)
        if not topic:
            return None
        if name is not None:
            topic["name"] = name
        if priority is not None:
            topic["priority"] = priority
        if hours is not None:
            topic["hours"] = hours
        return topic

    def _remove_topic_data(self, topic_id):
        """Remove a topic plus its tasks, quizzes, and quiz results."""
        self.topics.pop(topic_id, None)
        self.tasks = {
            tid: t for tid, t in self.tasks.items() if t["topic_id"] != topic_id
        }
        self.quizzes = {
            qid: q for qid, q in self.quizzes.items() if q["topic_id"] != topic_id
        }
        self.quiz_results = [r for r in self.quiz_results if r["topic_id"] != topic_id]

    def delete_topic(self, topic_id):
        if topic_id not in self.topics:
            return False
        self._remove_topic_data(topic_id)
        return True

  
    # Tasks (the study plan)
    
    def save_plan(self, tasks):
        """Replace old pending tasks with a new plan.
        Done and missed tasks stay as history."""
        self.tasks = {
            tid: t for tid, t in self.tasks.items() if t["status"] != "pending"
        }
        saved = []
        for task in tasks:
            task_id = self._new_id()
            self.tasks[task_id] = {**task, "id": task_id, "status": "pending"}
            saved.append(self.tasks[task_id])
        return saved

    def list_tasks(self, status=None, course_id=None):
        result = list(self.tasks.values())
        if status:
            result = [t for t in result if t["status"] == status]
        if course_id:
            result = [t for t in result if t["course_id"] == course_id]
        return sorted(result, key=lambda t: t["date"])

    def get_task(self, task_id):
        return self.tasks.get(task_id)

    def set_task_status(self, task_id, status):
        task = self.tasks.get(task_id)
        if task:
            task["status"] = status
        return task

    def delete_task(self, task_id):
        return self.tasks.pop(task_id, None) is not None

    def get_plan_summary(self):
        """Count tasks by status, plus the completion rate."""
        counts = {"pending": 0, "done": 0, "missed": 0}
        for task in self.tasks.values():
            counts[task["status"]] += 1
        finished = counts["done"] + counts["missed"]
        rate = round(counts["done"] / finished, 2) if finished else None
        return {"total": len(self.tasks), **counts, "completion_rate": rate}

   
    # Quizzes
    
    def add_quiz(self, topic_id, questions):
        quiz_id = self._new_id()
        stored = []
        for i, q in enumerate(questions):
            stored.append({**q, "id": f"{quiz_id}-{i}"})
        self.quizzes[quiz_id] = {
            "id": quiz_id,
            "topic_id": topic_id,
            "questions": stored,
            "submitted": False,
            "created_at": self._now(),
        }
        return self.quizzes[quiz_id]

    def get_quiz(self, quiz_id):
        return self.quizzes.get(quiz_id)

    def list_quizzes(self, topic_id=None):
        result = list(self.quizzes.values())
        if topic_id:
            result = [q for q in result if q["topic_id"] == topic_id]
        return result

    def add_quiz_result(self, topic_id, quiz_id, question_id, correct):
        self.quiz_results.append({
            "topic_id": topic_id,
            "quiz_id": quiz_id,
            "question_id": question_id,
            "correct": correct,
            "time": self._now(),
        })

    def list_quiz_results(self, topic_id=None):
        if topic_id:
            return [r for r in self.quiz_results if r["topic_id"] == topic_id]
        return list(self.quiz_results)

    
    # Revisions (plan changes proposed by the recovery agent)
    
    def add_revision(self, proposed_tasks, explanation, weak_topics=None):
        """Save a proposed new plan. The student must approve it before it is used."""
        revision_id = self._new_id()
        self.revisions[revision_id] = {
            "id": revision_id,
            "proposed_tasks": proposed_tasks,
            "explanation": explanation,          # why the plan changed
            "weak_topics": weak_topics or [],
            "status": "pending",                 # pending, approved, or rejected
            "created_at": self._now(),
        }
        return self.revisions[revision_id]

    def update_revision(self, revision_id, proposed_tasks=None, explanation=None):
        """Change the tasks or explanation of a revision that is still pending."""
        revision = self.revisions.get(revision_id)
        if not revision or revision["status"] != "pending":
            return None
        if proposed_tasks is not None:
            revision["proposed_tasks"] = proposed_tasks
        if explanation is not None:
            revision["explanation"] = explanation
        return revision

    def get_revision(self, revision_id):
        return self.revisions.get(revision_id)

    def list_revisions(self, status=None):
        result = list(self.revisions.values())
        if status:
            result = [r for r in result if r["status"] == status]
        return result

    def approve_revision(self, revision_id):
       # Mark as approved and make the proposed tasks the active plan.
        revision = self.revisions.get(revision_id)
        if not revision or revision["status"] != "pending":
            return None
        revision["status"] = "approved"
        self.save_plan(revision["proposed_tasks"])
        return revision

    def reject_revision(self, revision_id):
       #Mark as rejected. The current plan stays unchanged.
        revision = self.revisions.get(revision_id)
        if not revision or revision["status"] != "pending":
            return None
        revision["status"] = "rejected"
        return revision


#we center memoryStore to store every thing
store = MemoryStore()