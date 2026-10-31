import time


def call_with_retry(function, tries=4, wait_seconds=10):
    #Run function(). If Gemini is busy (503) or rate limited (429), wait and try again.
    for attempt in range(1, tries + 1):
        try:
            return function()
        except Exception as error:
            message = str(error)
            busy = "503" in message or "429" in message or "UNAVAILABLE" in message
            if not busy or attempt == tries:
                raise
            delay = wait_seconds * attempt
            print(f"[gemini] busy or rate limited, retrying in {delay}s (try {attempt}/{tries})")
            time.sleep(delay)