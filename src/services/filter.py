import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from config.logger import get_logger
from config.settings import JOBS_CACHE_FILE, RESUME_FILE, TOP_JOBS_FILE, MAX_WORKERS, TOP_K_PERCENTAGE, TOP_K_LLM
from src.core.parser import parse_resume
from src.core.embedder import get_embedding, save_cache, cache
from src.core.scorer import final_score
from src.core.reranker import batch_rerank
from src.core.applied_store import load_applied, is_applied

logger = get_logger("filter")

def filter_jobs():
    logger.info("Initializing Filter process...")
    applied_map = load_applied()

    try:
        with open(JOBS_CACHE_FILE, encoding="utf-8") as f:
            jobs = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load jobs cache. Pls run scraper first: {e}")
        return

    try:
        with open(RESUME_FILE, encoding="utf-8") as f:
            resume_text = f.read()
    except Exception as e:
        logger.error(f"Failed to load resume.txt. Does it exist?: {e}")
        return

    resume = parse_resume(resume_text)

    logger.info("Generating resume embedding")
    res_emb = get_embedding(resume_text)

    results = []
    start = time.time()
    skipped_applied = 0

    def process_job(jid, job):
        try:
            text = (job["title"] + " " + job.get("description", ""))[:2000]
            job_emb = get_embedding(text)
            score = final_score(resume, job, res_emb, job_emb)

            return {
                "id": jid,
                "title": job["title"],
                "score": score,
                "description": job.get("description", ""),
                "url": job.get("url", "")
            }
        except Exception as e:
            logger.error(f"Job failed {jid}: {e}")
            return None

    futures = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for jid, job in jobs.items():
            if is_applied(jid, applied_map):
                skipped_applied += 1
                continue

            futures.append(executor.submit(process_job, jid, job))

        for future in as_completed(futures):
            result = future.result()
            if result:
                results.append(result)

    logger.info(f"Skipped already applied jobs: {skipped_applied}")
    logger.info(f"Remaining jobs after filter: {len(results)}")
    logger.info(f"Scoring completed in {round(time.time()-start,2)} sec")

    if not results:
        logger.warning("No new jobs to rerank!")
        return

    # FILTER TOP %
    results.sort(key=lambda x: x["score"], reverse=True)
    top_jobs = results[:min(200, int(len(results)*TOP_K_PERCENTAGE))]

    logger.info(f"Filtered top {len(top_jobs)} jobs for LLM")

    # LLM RERANK
    logger.info("Starting LLM reranking...")
    llm_scores = batch_rerank(resume_text, top_jobs)

    # MERGE
    for job in top_jobs:
        job["llm_score"] = llm_scores.get(job["id"], job["score"])

    top_jobs.sort(key=lambda x: x["llm_score"], reverse=True)

    # Pick top K
    top_final = top_jobs[:TOP_K_LLM]

    # SAVE
    with open(TOP_JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump(top_final, f, indent=2)

    save_cache(cache)

    logger.info(f"✅ Top {len(top_final)} jobs saved to {TOP_JOBS_FILE}")
