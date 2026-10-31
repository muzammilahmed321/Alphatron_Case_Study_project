import json
import time

from google import genai
from google.genai import types

from app.core.config import settings
from app.utils.gemini_retry import call_with_retry
from app.utils.token_tracker import tracker


class QuizGenerator:
    #Asks Gemini to write multiple-choice questions from course material.

    def __init__(self, model=None):
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is missing in .env")
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = model or settings.gemini_model  

    def generate(self, topic_name, chunks, num_questions=3):
        # Put the retrieved passages into one block of text
        context = ""
        for chunk in chunks:
            context += f"[{chunk['source']}, page {chunk['page']}]\n{chunk['text']}\n\n"

        prompt = (
            f"Write {num_questions} multiple-choice questions about "
            f"'{topic_name}' using ONLY the course material below.\n"
            "Return ONLY a JSON list. Each item must have these keys:\n"
            '  "question": the question text,\n'
            '  "options": a list of exactly 4 answer strings,\n'
            '  "correct_index": the position (0 to 3) of the right answer,\n'
            '  "explanation": one sentence explaining the right answer.\n\n'
            f"Course material:\n{context}"
        )

        start = time.time()
        response = call_with_retry(lambda: self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.4,
                response_mime_type="application/json",
            ),
        ))
        seconds = time.time() - start

        questions = self._parse(response.text)

        usage = response.usage_metadata
        input_tokens = getattr(usage, "prompt_token_count", 0) or 0
        output_tokens = getattr(usage, "candidates_token_count", 0) or 0
        tracker.record("quiz", input_tokens, output_tokens, seconds)

        return {
            "questions": questions,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        }

    def _parse(self, text):
        # Remove json fences if the model added them
        text = (text or "").strip().replace("```json", "").replace("```", "").strip()
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            raise ValueError("Gemini did not return valid JSON")

        # Keep only well-formed questions
        good = []
        for item in data:
            options = item.get("options", [])
            index = item.get("correct_index")
            if (
                item.get("question")
                and len(options) == 4
                and isinstance(index, int)
                and 0 <= index <= 3
            ):
                good.append({
                    "question": item["question"],
                    "options": options,
                    "correct_index": index,
                    "explanation": item.get("explanation", ""),
                })

        if not good:
            raise ValueError("No valid questions were generated")
        return good