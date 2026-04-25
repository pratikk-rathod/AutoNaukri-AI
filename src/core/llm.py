import requests
from config.logger import get_logger
from config.settings import OLLAMA_API_URL, LLM_MODEL
from tenacity import retry, wait_exponential, stop_after_attempt

logger = get_logger("llm")

@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3))
def ask_llm(resume, question):
    prompt = f"""
Answer in MAX 1-2 words ONLY.

Rules:
- No explanation
- Prefer: Yes / No / Immediate / Mumbai
- If unsure → Yes

Resume:
{resume}

Question:
{question}

Answer:
"""
    try:
        res = requests.post(
            f"{OLLAMA_API_URL}/api/generate",
            json={
                "model": LLM_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1}
            },
            timeout=60
        )
        res.raise_for_status()

        out = res.json().get("response", "").strip()
        logger.info(f"🧠 LLM RAW: {out}")
        return out

    except Exception as e:
        logger.error(f"❌ LLM failed: {e}")
        raise e  # Tenacity handles retries only if exception is raised
