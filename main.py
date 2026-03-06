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

import logging
import time

from utils.utils import start_logger
from pipeline.flow import pipeline

logger = start_logger(__name__)


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