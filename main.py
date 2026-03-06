"""
main.py — Entry point for Operation Restore Uber Account.

The full pipeline (crawl → clean → send) is orchestrated by Prefect.
Each stage runs as an independently retried task with state tracked locally.

Run once:
    python main.py

Or run directly from the flow module (same effect):
    python -m pipeline.flow

To start the Prefect dashboard:
    prefect server start  →  http://localhost:4200
"""

import time
from utils import setup_logging

# IMPORTANT: setup_logging() calls load_dotenv() internally.
# It MUST run before any other project import, because crawler_linkedin.py
# and email_sender.py read os.getenv() at module level (line 15, 13 etc.).
# Python executes module-level code at import time — if load_dotenv() hasn't
# fired yet, every os.getenv() call returns None.
logger = setup_logging()

from pipeline.flow import pipeline


if __name__ == '__main__':
    logger.info('=== Operation Restore Uber Account — pipeline starting ===')
    start = time.monotonic()
    try:
        pipeline()
        elapsed = time.monotonic() - start
        logger.info(f'=== Pipeline completed successfully in {elapsed:.1f}s ===')
    except Exception:
        elapsed = time.monotonic() - start
        logger.exception(f'=== Pipeline FAILED after {elapsed:.1f}s ===')
        raise