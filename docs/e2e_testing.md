# End-to-End Testing Guide

> [!NOTE]
> The LinkedIn crawler targets the **2020 People search interface**, which no longer exists.
> The E2E strategies below are preserved for reference and remain valid for any future
> re-implementation of the data collection layer. Everything below the crawler
> (cleaning, email factory, sending, Prefect orchestration) is fully testable today.

---

## Why Full E2E Tests Are Hard Here

This project sits at the intersection of three things that resist automation testing:

| Factor | Challenge |
|--------|-----------|
| **Live LinkedIn** | Real credentials, bot detection, rate limits, outdated DOM (2020 UI) |
| **Real Chrome browser** | Selenium tests are slow, flaky, environment-dependent |
| **Gmail SMTP** | Sending real emails as a test side-effect is unacceptable |

Standard unit tests (the 103 in `tests/`) cover all pure logic. E2E tests cover the seams
between components — and require deliberate design to be repeatable.

---

## What You Can Test Today (No LinkedIn Required)

The following layers are fully functional and testable without a live LinkedIn session:

### ✅ Data Cleaning
```bash
# Drop sample JSON into data_raw/ and run:
python -c "from data_cleaning import clean_data; print(clean_data([{'name': 'John Doe', 'position': 'Engineer at Uber'}]))"
```

### ✅ Email Factory
```bash
pytest tests/test_email_factory.py -v
```

### ✅ Prefect Pipeline Wiring (mocked tasks)
```python
# tests/e2e/test_flow_e2e.py
import pytest
from unittest.mock import patch

@pytest.mark.e2e
def test_pipeline_flow_executes_all_tasks():
    """Verify the full Prefect pipeline calls crawl → clean → send in order."""
    call_order = []

    with patch('pipeline.flow.crawl_task', side_effect=lambda *a, **kw: call_order.append('crawl') or []), \
         patch('pipeline.flow.clean_task', side_effect=lambda *a, **kw: call_order.append('clean') or []), \
         patch('pipeline.flow.send_task', side_effect=lambda *a, **kw: call_order.append('send')):

        from pipeline.flow import pipeline
        pipeline(cities=['San Francisco'], companies=['Uber'], num_pages=1)

    assert call_order == ['crawl', 'clean', 'send']
```

### ✅ Mock SMTP (Email Sending Without Real Gmail)
```python
# tests/e2e/test_email_e2e.py
import pytest
from aiosmtpd.controller import Controller
from aiosmtpd.handlers import Sink
from email_sender import EmailSender
from unittest.mock import patch

@pytest.fixture(scope='module')
def smtp_server():
    controller = Controller(Sink(), hostname='127.0.0.1', port=1025)
    controller.start()
    yield controller
    controller.stop()

@pytest.mark.e2e
def test_email_sender_connects_and_sends(smtp_server, monkeypatch):
    monkeypatch.setenv('USERNAME_EMAIL', 'test@example.com')
    monkeypatch.setenv('PASSWORD_EMAIL', 'pass')

    with patch('smtplib.SMTP.login', return_value=None), \
         patch('smtplib.SMTP.starttls', return_value=None), \
         patch('smtplib.SMTP.send_message', return_value=None), \
         patch('smtplib.SMTP.quit', return_value=None):
        sender = EmailSender()
        sender.send_email([{'name': 'Test User'}])
```

---

## LinkedIn Crawler E2E (Historical Reference)

> [!WARNING]
> The strategies below are **not executable** against the current LinkedIn UI.
> They are preserved as a reference for anyone who re-implements `_crawl_city()`
> against LinkedIn's current company people page + infinite scroll interface.

### Why the Crawler Can't Be E2E Tested Today

1. **LinkedIn changed their search interface after 2020.** The crawler targets a paginated
   global People search that no longer exists. The current interface uses company-specific
   `/company/{name}/people/` pages with location filters and infinite scroll.

2. **Email verification is a manual step.** LinkedIn triggers a 6-digit email challenge
   on every fresh browser session. While `CHROME_PROFILE_DIR` solves this for local runs
   (complete verification once, session persists), it is incompatible with Docker or CI:
   - Docker containers are ephemeral — no state persists without a volume mount
   - Even with a volume, the *initial* verification requires a GUI (Chrome is graphical)
   - Fully automated verification would require IMAP access to parse the code from email

3. **`_crawl_city()` would need a full rewrite** before any of the strategies below
   are applicable again.

### Previously Working Strategy — Selenium with Staging Account

```python
# tests/e2e/test_crawl_e2e.py  (outdated — for reference only)
import pytest
from crawler.crawler_linkedin import LinkedInCrawler

@pytest.mark.e2e
def test_crawl_one_page():
    results = LinkedInCrawler.get_data(
        cities=['San Francisco'],
        companies=['Uber'],
        num_pages=1,
    )
    assert isinstance(results, list)
    assert len(results) > 0
    assert all('name' in r and 'position' in r for r in results)
```

> Setup would require a dedicated throwaway LinkedIn account and `CHROME_PROFILE_DIR`
> configured to survive the initial verification challenge. See `.env.example`.

---

## Recommended Manual Validation (Non-Crawler Layers)

When validating the non-crawler pipeline end-to-end:

```
Step 1: Unit tests (offline, always CI-safe)
    → pytest tests/ -v
    → All 103 tests should pass

Step 2: Data cleaning against real raw data
    → Place JSON files in data_raw/
    → python -c "from data_cleaning.data_cleaning import clean_data; ..."
    → Confirm data_cleaned/ has fewer records (filters applied)

Step 3: Dry-run email (send to yourself only)
    → Temporarily set EMAIL_TARGET=1 and your own address in the recipient list
    → python -m pipeline.flow  (with mocked crawl data)
    → Confirm you receive the email

Step 4: Prefect run state
    → prefect server start
    → Navigate to http://localhost:4200 → verify all tasks show COMPLETED
```

---

## What Each Layer Tests

```
┌─────────────────────────────────────────────────────────────────┐
│              End-to-End (E2E) — future re-implementation        │
│  Crawler → clean → SMTP → email received (requires new crawler) │
├─────────────────────────────────────────────────────────────────┤
│              Integration (mock SMTP + mock crawler)             │
│  Real pipeline wiring, real cleaning, real email formatting     │
├─────────────────────────────────────────────────────────────────┤
│                   Unit (103 tests ✅ today)                      │
│  EmailFactory, Conditions, ProxyRotator, utils,                 │
│  crawler parallelism + driver lifecycle (mocked)                │
└─────────────────────────────────────────────────────────────────┘
```

The unit tests cover the bulk of the logic. The crawler E2E layer requires a
re-implementation of `_crawl_city()` before it can be exercised again.
