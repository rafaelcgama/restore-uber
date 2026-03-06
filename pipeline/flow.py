"""
pipeline/flow.py — Prefect workflow definition for Operation Restore Uber Account.

Run the full pipeline:
    python -m pipeline.flow

Start the Prefect UI (optional):
    prefect server start

Schedule via Prefect (replaces cron):
    pipeline.serve(name="daily-run", cron="0 6 * * *")
"""

import logging

from prefect import flow, task

from crawler import LinkedInCrawler
from data_cleaning import clean_data
from email_sender import EmailSender
from utils import setup_logging

logger = logging.getLogger(__name__)


# ── Tasks ────────────────────────────────────────────────────────────────────

@task(
    name="crawl-linkedin",
    retries=3,
    retry_delay_seconds=60,
    description="Crawls LinkedIn for Uber employee names and titles.",
)
def crawl_task(cities: list[str], companies: list[str], num_pages: int | None = None) -> list:
    """
    Run the LinkedIn crawler for all city/company combinations.

    Prefect will automatically retry this task up to 3 times (with a 60-second
    delay between attempts) before marking the run as failed.  All other tasks
    in the flow are unaffected by a crawl failure.

    :param cities: List of city names to search.
    :param companies: List of company names to search.
    :param num_pages: Optional cap on pages scraped per combination (useful for testing).
    :return: Flat list of employee dicts with ``name`` and ``position`` keys.
    """
    logger.info(f'Starting crawl for cities={cities}, companies={companies}')
    raw_data = LinkedInCrawler.get_data(cities, companies, num_pages=num_pages)
    logger.info(f'Crawl complete — {len(raw_data)} raw records collected')
    return raw_data


@task(
    name="clean-data",
    description="Filters raw employee records, removing ex-employees, drivers, and placeholders.",
)
def clean_task(raw_data: list) -> list:
    """
    Apply data-cleaning rules to the raw crawler output.

    :param raw_data: List of dicts from :func:`crawl_task`.
    :return: Filtered list of employee dicts.
    """
    cleaned = clean_data(raw_data)
    logger.info(f'Data cleaning complete — {len(raw_data)} → {len(cleaned)} records')
    return cleaned


@task(
    name="send-emails",
    retries=2,
    retry_delay_seconds=30,
    description="Sends personalised emails to every cleaned employee record.",
)
def send_task(cleaned_data: list) -> None:
    """
    Dispatch emails to the cleaned employee list.

    :param cleaned_data: List of employee dicts from :func:`clean_task`.
    """
    logger.info(f'Starting email dispatch for {len(cleaned_data)} employees')
    sender = EmailSender()
    sender.send_email(cleaned_data)
    logger.info('Email dispatch complete')


# ── Flow ─────────────────────────────────────────────────────────────────────

@flow(
    name="restore-uber-pipeline",
    log_prints=True,
    description=(
            "End-to-end pipeline: crawl LinkedIn → clean data → send emails.\n"
            "Each stage is independently retried on failure. State is persisted "
            "in Prefect's local SQLite backend so partial-failure runs can be "
            "resumed without re-running successful tasks."
    ),
)
def pipeline(
        cities: list[str] | None = None,
        companies: list[str] | None = None,
        num_pages: int | None = None,
) -> None:
    """
    Orchestrate the full workflow.

    :param cities: Cities to crawl. Defaults to São Paulo + San Francisco.
    :param companies: Companies to filter on. Defaults to Uber.
    :param num_pages: Optional page cap (useful for smoke-testing without a full run).
    """
    if cities is None:
        cities = ['São Paulo', 'San Francisco']
    if companies is None:
        companies = ['Uber']

    raw_data = crawl_task(cities, companies, num_pages)
    cleaned_data = clean_task(raw_data)
    send_task(cleaned_data)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    setup_logging()
    pipeline()
