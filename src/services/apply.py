import requests
import time
import random
import json
from playwright.async_api import async_playwright
from tenacity import retry, wait_exponential, stop_after_attempt

from config.logger import get_logger
from config.settings import (
    NAUKRI_EMAIL, NAUKRI_PASSWORD, NAUKRI_APPLY_API_URL, 
    RESUME_FILE, TOP_JOBS_FILE, ANSWERS_DEFAULTS
)
from src.core.llm import ask_llm
from src.core.utils import load_kb, save_kb, clean_answer, load_format_map, save_format_map
from src.core.applied_store import load_applied, save_applied, add_applied

class QuotaExceededError(Exception):
    pass

logger = get_logger("auto_apply")
applied_map = load_applied()

@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3))
async def get_auth_token():
    if not NAUKRI_EMAIL or not NAUKRI_PASSWORD:
        logger.error("❌ NAUKRI_EMAIL or NAUKRI_PASSWORD missing from environment variables")
        return None

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        logger.info("🔐 Logging into Naukri...")

        await page.goto("https://www.naukri.com/nlogin/login")
        await page.fill("#usernameField", NAUKRI_EMAIL)
        await page.fill("#passwordField", NAUKRI_PASSWORD)
        await page.click("button[type='submit']")

        await page.wait_for_timeout(5000)

        cookies = await context.cookies()

        for c in cookies:
            if c["name"] == "nauk_at":
                logger.info("✅ Token extracted")
                await browser.close()
                return c["value"]

        logger.error("❌ Token not found")
        await browser.close()
        raise ValueError("Failed to retrieve nauk_at token from cookies")

def build_payload(job_ids):
    return {
        "strJobsarr": job_ids,
        "src": "NAUKRI_APPLY",
        "applySrc": "drecomm_profile",
        "logstr": "drecomm",
        "applyTypeId": "107",
        "crossdomain": False,
        "jquery": 1,
        "chatBotSD": True
    }

def generate_answer(q, defaults, kb, resume):
    q_text = (q.get("questionName") or "").lower()

    logger.info(f"🧠 Generating answer for: {q_text}")

    if "relocate" in q_text:
        return "Yes"
    if "notice" in q_text:
        return defaults.get("noticePeriod", "Immediate")
    if "ctc" in q_text:
        return defaults.get("expectedCtc", "1500000")
    if "experience" in q_text:
        return defaults.get("experience", "1")

    if q_text in kb:
        logger.info("📚 Using KB answer")
        return kb[q_text]

    raw = ask_llm(resume, q_text)
    cleaned = clean_answer(raw)

    logger.info(f"➡️ Final Answer: {cleaned}")

    kb[q_text] = cleaned
    return cleaned

def execute_batch_apply(payload, headers):
    res = requests.post(NAUKRI_APPLY_API_URL, headers=headers, json=payload, timeout=30)
    try:
        res.raise_for_status()
    except Exception as e:
        if "quota" in res.text.lower():
            raise QuotaExceededError("Naukri Daily Quota Exceeded")
        logger.error(f"HTTP Error: {e} | Response Body: {res.text}")
        raise e
    return res.json()

def apply_jobs(job_ids, token, defaults, resume, job_lookup=None):
    kb = load_kb()
    format_map = load_format_map()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "appid": "105",
        "clientid": "d3skt0p",
        "systemid": "jobseeker",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Origin": "https://www.naukri.com",
        "Referer": "https://www.naukri.com/"
    }

    success, failed, skipped = 0, 0, 0

    for i in range(0, len(job_ids), 5):
        batch = job_ids[i:i+5]
        logger.info(f"\n📦 Batch {i//5+1}: {batch}")

        try:
            data = execute_batch_apply(build_payload(batch), headers)
            logger.info(f"🌐 API Status OK for initial batch.")
        except QuotaExceededError:
            logger.critical("🛑 Daily application quota exceeded! Halting the pipeline for today.")
            break
        except Exception as e:
            logger.error(f"❌ REQUEST FAIL: {e}")
            continue

        retry_payload = {}

        for job in data.get("jobs", []):
            jid = job["jobId"]
            status = job.get("status")

            logger.info(f"🔎 JOB {jid} | STATUS: {status}")

            if status == 200:
                logger.info(f"✅ SUCCESS: {jid}")
                success += 1

                job_data = job_lookup.get(jid, {}) if job_lookup else {}
                add_applied({
                    "job_id": jid,
                    "title": job_data.get("title"),
                    "url": job_data.get("url"),
                    "description": job_data.get("description")
                }, applied_map)

                logger.info(f"💾 STORED APPLIED: {jid}")
                continue

            elif status == 409001:
                logger.info(f"⏭️ ALREADY APPLIED: {jid}")
                skipped += 1
                continue

            elif job.get("questionnaire"):
                logger.warning(f"⚠️ QUESTIONS REQUIRED: {jid}")
                answers = {}

                for q in job["questionnaire"]:
                    qid = str(q["questionId"])
                    ans = generate_answer(q, defaults, kb, resume)

                    # Apply learned format
                    if format_map.get(qid) == "list":
                        ans = [ans]
                    if format_map.get(qid) == "number":
                        ans = str(ans) if str(ans).isdigit() else "1"

                    answers[qid] = ans

                retry_payload[jid] = {"answers": answers}
            else:
                logger.error(f"❌ FAILED WITHOUT QUESTION: {jid}")
                failed += 1

        # RETRY LOGIC for questions
        if retry_payload:
            payload2 = build_payload(list(retry_payload.keys()))
            payload2["applyData"] = retry_payload

            logger.info(f"🔁 Retrying jobs with answers: {list(retry_payload.keys())}")

            try:
                data2 = execute_batch_apply(payload2, headers)
            except Exception as e:
                logger.error(f"❌ FAILED RETRY BATCH: {e}")
                data2 = {}

            for job in data2.get("jobs", []):
                jid = job["jobId"]

                if job.get("status") == 200:
                    logger.info(f"✅ SUCCESS AFTER RETRY: {jid}")
                    success += 1
                    job_data = job_lookup.get(jid, {}) if job_lookup else {}
                    add_applied({"job_id": jid, "title": job_data.get("title")}, applied_map)
                    continue

                if job.get("validationError"):
                    logger.warning(f"⚠️ Learning schema for {jid}")
                    errors = job["validationError"]
                    answers = retry_payload[jid]["answers"]

                    for err in errors:
                        qid = str(err["field"])
                        msg = err.get("message", "").lower()

                        if "list" in msg:
                            format_map[qid] = "list"
                            answers[qid] = [answers[qid]]
                        elif "number" in msg:
                            format_map[qid] = "number"
                            answers[qid] = "1"

                    # Ultimate retry
                    payload3 = build_payload([jid])
                    payload3["applyData"] = {jid: {"answers": answers}}

                    try:
                        data3 = execute_batch_apply(payload3, headers)
                        for j3 in data3.get("jobs", []):
                            if j3.get("status") == 200:
                                logger.info(f"✅ LEARNED SUCCESS: {jid}")
                                success += 1
                                job_data = job_lookup.get(jid, {}) if job_lookup else {}
                                add_applied({"job_id": jid, "title": job_data.get("title")}, applied_map)
                            else:
                                logger.error(f"❌ FINAL FAIL: {j3}")
                                failed += 1
                    except Exception as e:
                        logger.error(f"❌ FINAL FAIL REQUEST ERROR: {e}")
                        failed += 1
                else:
                    logger.error(f"❌ FAILED AFTER RETRY: {jid}")
                    failed += 1

        time.sleep(random.uniform(1, 3))

    save_kb(kb)
    save_format_map(format_map)
    save_applied(applied_map)

    logger.info("\n🎯 FINAL SUMMARY")
    logger.info(f"✅ Success: {success}")
    logger.info(f"❌ Failed: {failed}")
    logger.info(f"⏭️ Skipped: {skipped}")

async def start_apply_flow():
    try:
        with open(TOP_JOBS_FILE, encoding='utf-8') as f:
            jobs = json.load(f)
    except Exception as e:
        logger.error(f"No top jobs found. Did you run filter?: {e}")
        return

    try:
        with open(RESUME_FILE, encoding='utf-8') as f:
            resume = f.read()
    except Exception as e:
        logger.error(f"No resume found.: {e}")
        return

    job_ids = [j["id"] for j in jobs]
    if not job_ids:
        logger.warning("No jobs to apply to.")
        return

    token = await get_auth_token()
    if not token:
        return

    job_lookup = {j["id"]: j for j in jobs}
    apply_jobs(job_ids, token, ANSWERS_DEFAULTS, resume, job_lookup)
