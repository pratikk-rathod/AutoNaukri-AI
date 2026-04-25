import requests
import json
import re
from config.logger import get_logger
from config.settings import OLLAMA_API_URL, LLM_MODEL
from tenacity import retry, wait_exponential, stop_after_attempt

logger = get_logger("reranker")

def extract_json(text):
    try:
        return json.loads(text)
    except:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                return {}
    return {}

@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3))
def batch_rerank_internal(prompt):
    res = requests.post(
        f"{OLLAMA_API_URL}/api/generate",
        json={
            "model": LLM_MODEL,
            "prompt": prompt,
            "stream": False
        },
        timeout=120
    )
    res.raise_for_status()
    output = res.json()["response"]
    parsed = extract_json(output)
    if not parsed:
        raise ValueError("Failed to parse JSON from LLM response")
    return parsed


def batch_rerank(resume_text, jobs, batch_size=3):
    scores = {}

    for i in range(0, len(jobs), batch_size):
        batch = jobs[i:i+batch_size]
        logger.info(f"LLM batch {i//batch_size + 1}/{len(jobs)//batch_size + 1}")

        batch_text = "\n\n".join([
            f"ID: {j['id']}\nTITLE: {j['title']}\nDESC: {j['description'][:150]}"
            for j in batch
        ])

        prompt = f"""
You are a strict JSON API.

Return ONLY:
{{"job_id": score}}

Resume:
{resume_text}

Jobs:
{batch_text}
"""
        
        try:
            parsed = batch_rerank_internal(prompt)
            scores.update(parsed)
        except Exception as e:
            logger.warning(f"Failed LLM batch after retries: {e}")

    return scores
