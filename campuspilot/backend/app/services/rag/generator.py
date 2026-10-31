import time

from google import genai
from google.genai import types

from app.core.config import settings
from app.utils.gemini_retry import call_with_retry
from app.utils.token_tracker import tracker


class AnswerGenerator:
    #Asks Gemini to answer a question using only the chunks we give it.

    def __init__(self, model=None):
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is missing in .env")

        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = model or settings.gemini_model

    def answer(self, question, chunks):
        # Turn the chunks into one block of text, labelled with source and page
        context = ""
        for chunk in chunks:
            context += f"[{chunk['source']}, page {chunk['page']}]\n{chunk['text']}\n\n"

        system_prompt = (
            "You are a study assistant. Answer the question using ONLY the "
            "course material provided. After each fact, cite the source like "
            "[filename, page X]. If the material does not contain the answer, "
            "say you could not find it in the uploaded documents."
        )

        user_message = f"Course material:\n{context}\nQuestion: {question}"

        start = time.time()
        response = call_with_retry(lambda: self.client.models.generate_content(
            model=self.model,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.2,
            ),
        ))
        seconds = time.time() - start

        usage = response.usage_metadata
        input_tokens = getattr(usage, "prompt_token_count", 0) or 0
        output_tokens = getattr(usage, "candidates_token_count", 0) or 0

        tracker.record("chat", input_tokens, output_tokens, seconds)

        return {
            "answer": response.text or "No answer was generated.",
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "seconds": round(seconds, 2),
        }