import asyncio
import json
import re
from playwright.async_api import async_playwright
from tenacity import retry, stop_after_attempt, wait_fixed
from config.logger import get_logger
from config.settings import JOBS_CACHE_FILE, JOBS_TEXT_FILE, NAUKRI_BASE_SEARCH_URL, MUST_HAVE_SKILLS, DEALBREAKERS

logger = get_logger("scraper")

def clean_text(html, limit=600):
    if not html:
        return "No description"
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:limit] + "... [TRUNCATED]" if len(text) > limit else text

def is_relevant(title, desc, tags):
    combined = f"{title} {desc} {tags}".lower()
    if any(bad in combined for bad in DEALBREAKERS):
        return False
    if any(skill in combined for skill in MUST_HAVE_SKILLS):
        return True
    return False

@retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
async def scrape():
    scraped_jobs = {}
    current_page = 0
    total_pages = None

    api_event = asyncio.Event()

    logger.info("🚀 Starting Scraping Process...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )

        context = await browser.new_context()
        page = await context.new_page()

        # Prevent new tabs (job clicks etc.)
        page.on("popup", lambda popup: asyncio.create_task(popup.close()))

        # STEALTH
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US','en'] });
        """)

        # API INTERCEPT
        async def handle_response(response):
            nonlocal current_page, total_pages

            if "jobapi/v3/search" in response.url:
                try:
                    data = await response.json()

                    jobs = data.get("jobDetails", [])
                    if not jobs:
                        return

                    current_page = data.get("pageNo", current_page)
                    if data.get("totalPages"):
                        total_pages = data.get("totalPages")

                    logger.info(f"📄 Page {current_page}/{total_pages}")

                    for job in jobs:
                        job_id = job.get("jobId")
                        title = job.get("title")
                        raw_desc = job.get("jobDescription", "")
                        tags = job.get("tagsAndSkills", "")
                        jd_url = job.get("jdURL", "")
                        full_url = "https://www.naukri.com" + jd_url if jd_url else None

                        desc = clean_text(raw_desc)

                        if is_relevant(title, desc, tags):
                            if job_id and job_id not in scraped_jobs:
                                scraped_jobs[job_id] = {
                                    "title": title,
                                    "description": desc,
                                    "skills": tags,
                                    "url": full_url
                                }
                                logger.info(f"✅ {job_id} | {title}")
                        else:
                            logger.info(f"❌ {job_id} | {title}")

                    api_event.set()

                except Exception as e:
                    logger.warning(f"⚠️ API parse error: {e}")

        page.on("response", handle_response)

        # START URL
        logger.info("🚀 Opening Naukri...")
        await page.goto(NAUKRI_BASE_SEARCH_URL, wait_until="domcontentloaded")

        try:
            await asyncio.wait_for(api_event.wait(), timeout=20)
        except asyncio.TimeoutError:
            logger.warning("⚠️ Initial API timeout")
        api_event.clear()

        # PAGINATION LOOP (ROBUST)
        MAX_ATTEMPTS = 20

        while True:
            if total_pages and current_page >= total_pages:
                logger.info("✅ Reached last page")
                break

            logger.info("➡️ Finding correct Next button...")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1500)

            candidates = page.locator('a[href*="-jobs-"]:has-text("Next")')
            count = await candidates.count()

            if count == 0:
                logger.warning("❌ No Next candidates found")
                break

            success = False
            for i in range(min(count, MAX_ATTEMPTS)):
                try:
                    btn = candidates.nth(i)
                    logger.info(f"🔁 Attempt {i+1}")
                    api_event.clear()

                    await btn.scroll_into_view_if_needed()
                    await btn.click(force=True)

                    await asyncio.wait_for(api_event.wait(), timeout=8)

                    logger.info("✅ Correct Next clicked")
                    success = True
                    break

                except asyncio.TimeoutError:
                    logger.warning("⚠️ Wrong Next (no API), retrying...")
                    continue
                except Exception as e:
                    logger.warning(f"⚠️ Click error: {e}")
                    continue

            if not success:
                logger.warning("❌ Could not find valid Next → stopping")
                break

        await asyncio.sleep(5)

        logger.info(f"💾 Saving {len(scraped_jobs)} jobs")

        with open(JOBS_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(scraped_jobs, f, indent=2, ensure_ascii=False)

        with open(JOBS_TEXT_FILE, "w", encoding="utf-8") as f:
            for jid, job in scraped_jobs.items():
                f.write(f"JOB ID: {jid}\n")
                f.write(f"URL: {job.get('url','')}\n")
                f.write(f"TITLE: {job['title']}\n")
                f.write(f"SKILLS: {job['skills']}\n")
                f.write(f"DESC: {job['description']}\n")
                f.write("=" * 80 + "\n")

        logger.info("✅ Done Scraping")
        await browser.close()
