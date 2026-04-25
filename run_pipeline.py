import argparse
import asyncio
from config.logger import get_logger
from src.services.scraper import scrape
from src.services.filter import filter_jobs
from src.services.apply import start_apply_flow

logger = get_logger("pipeline")

async def run_all():
    logger.info("====================================")
    logger.info("🚀 STARTING AUTOMATED JOB PIPELINE 🚀")
    logger.info("====================================")

    logger.info("--- PHASE 1: SCRAPING ---")
    await scrape()
    
    logger.info("--- PHASE 2: FILTER & RERANK ---")
    filter_jobs()
    
    logger.info("--- PHASE 3: AUTO APPLY ---")
    await start_apply_flow()

    logger.info("====================================")
    logger.info("✅ PIPELINE EXECUTION COMPLETE ✅")
    logger.info("====================================")

def main():
    parser = argparse.ArgumentParser(description="Automated Job Application Pipeline")
    parser.add_argument("--scrape", action="store_true", help="Run scraping phase only")
    parser.add_argument("--filter", action="store_true", help="Run filtering and AI ranking phase only")
    parser.add_argument("--apply", action="store_true", help="Run auto-apply phase only")
    parser.add_argument("--all", action="store_true", help="Run the entire pipeline (Scrape -> Filter -> Apply)")

    args = parser.parse_args()

    try:
        if args.scrape:
            asyncio.run(scrape())
        elif args.filter:
            filter_jobs()
        elif args.apply:
            asyncio.run(start_apply_flow())
        elif args.all:
            asyncio.run(run_all())
        else:
            parser.print_help()
            logger.info("No specific phase selected. Run with --all to execute the complete pipeline.")
            
    except KeyboardInterrupt:
        logger.warning("\nPipeline forced to stop by user. Exiting gracefully.")
    except Exception as e:
        logger.exception(f"Pipeline encountered a critical error: {e}")

if __name__ == "__main__":
    main()
