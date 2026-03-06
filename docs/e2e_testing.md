# End-to-End Testing Guide

## Why E2E Tests Are Hard Here

This project sits at the intersection of three things that resist automation testing:

| Factor | Challenge |
|--------|-----------| 
| **Live LinkedIn** | Real credentials, bot detection, rate limits, dynamic DOM |
| **Real Chrome browser** | Selenium tests are slow, flaky, environment-dependent |
| **Gmail SMTP** | Sending real emails as a test side-effect is unacceptable |

Standard unit tests (the 96 in `tests/`) cover all pure logic. E2E tests cover the seams between components — and require deliberate design to be repeatable.

---

## Strategy 1 — Recorded/Replayed HTTP with VCR.py *(best for crawler)*

[`vcrpy`](https://vcrpy.readthedocs.io/) records real HTTP interactions to a YAML "cassette" file, then replays them offline. This works for `requests`-based code but **not for Selenium** (which drives a browser, not raw HTTP).

**What works:**
- Email SMTP can be tested with `aiosmtpd` or SMTP4Dev (see Strategy 3)
- API-based components (if any are added later)

---

## Strategy 2 — Selenium with a Staging LinkedIn Account *(best for crawler)*

> [!IMPORTANT]
> Use a **dedicated throwaway LinkedIn account** — not your personal one. LinkedIn may ban accounts used for automated access.

### Setup

1. Create a sandboxed LinkedIn account (e.g., `test.crawler.2024@gmail.com`)
2. Add credentials to `.env.test`:
   ```
   USERNAME_LINKEDIN=test.crawler.2024@gmail.com
   PASSWORD_LINKEDIN=<password>
   ```
3. Install a local Chrome + matching ChromeDriver in CI via:
   ```bash
   pip install webdriver-manager
   ```
   Replace `uc.Chrome()` with `uc.Chrome(driver_executable_path=ChromeDriverManager().install())` in `driver_functions.py`.

### Minimal E2E Crawl Test

```python
# tests/e2e/test_crawl_e2e.py
import pytest
from crawler.crawler_linkedin import LinkedInCrawler

@pytest.mark.e2e
def test_crawl_one_page():
    """Crawl exactly 1 page from San Francisco — should return > 0 records."""
    crawler = LinkedInCrawler()
    results = crawler.get_data(
        cities=['San Francisco'],
        companies=['Uber'],
        num_pages=1,    # limit to one page to keep CI fast
    )
    assert isinstance(results, list)
    assert len(results) > 0
    assert all('name' in r and 'position' in r for r in results)
```

Run only E2E tests (skip in CI unless explicitly opted-in):
```bash
pytest tests/e2e/ -m e2e -v
```

Mark in `pytest.ini`:
```ini
[pytest]
markers =
    e2e: end-to-end tests requiring live credentials (deselect with -m "not e2e")
```

---

## Strategy 3 — Mock SMTP Server for Email Tests

Use [`aiosmtpd`](https://aiosmtpd.readthedocs.io) to run a local fake SMTP server that captures outgoing emails without sending them.

```python
# tests/e2e/test_email_e2e.py
import pytest
import threading
from aiosmtpd.controller import Controller
from aiosmtpd.handlers import Sink
from email_sender import EmailSender

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
    monkeypatch.setattr('smtplib.SMTP.login', lambda *a, **kw: None)

    sender = EmailSender()
    # Patch to use local server
    with patch('smtplib.SMTP.__init__', lambda self, host, port: None):
        sender.send_email([{'name': 'Test User'}])
```

---

## Strategy 4 — Prefect Flow Integration Test

Test that all three tasks are wired up correctly and data flows between them, using mocked task functions:

```python
# tests/e2e/test_flow_e2e.py
import pytest
from unittest.mock import patch, MagicMock

@pytest.mark.e2e
def test_pipeline_flow_executes_all_tasks():
    """Verify the full Prefect pipeline calls crawl → clean → send in order."""
    call_order = []

    with patch('pipeline.flow.crawl_task', side_effect=lambda *a, **kw: call_order.append('crawl') or []) as mc, \
         patch('pipeline.flow.clean_task', side_effect=lambda *a, **kw: call_order.append('clean') or []) as ml, \
         patch('pipeline.flow.send_task', side_effect=lambda *a, **kw: call_order.append('send')) as ms:

        from pipeline.flow import pipeline
        pipeline(cities=['San Francisco'], companies=['Uber'], num_pages=1)

    assert call_order == ['crawl', 'clean', 'send']
```

---

## Recommended E2E Protocol (Manual)

When you want to validate the full pipeline for real — say, before pointing it at a new company:

```
Step 1: Smoke-crawl (1 page, sandboxed account)
    → python3 -m pipeline.flow  # with num_pages=1 in flow.py temporarily
    → Confirm data_raw/ has a JSON file with > 0 records

Step 2: Verify data cleaning
    → python3 data_cleaning/data_cleaning.py
    → Confirm data_cleaned/ has fewer records than data_raw/ (filtering worked)

Step 3: Dry-run email (send to yourself only)
    → In email_sender.py, replace the recipient loop with a single hardcoded test address
    → Confirm you receive the email

Step 4: Check Prefect run state
    → prefect server start
    → Navigate to http://localhost:4200 → verify all tasks show COMPLETED
```

---

## What Each Layer Tests

```
┌─────────────────────────────────────────────────────────────┐
│                    End-to-End (E2E)                         │
│  Real LinkedIn login → crawl → clean → SMTP → email rcvd   │
├─────────────────────────────────────────────────────────────┤
│                  Integration (Strategy 3/4)                 │
│  Mocked SMTP + mocked LinkedIn + real pipeline wiring       │
├─────────────────────────────────────────────────────────────┤
│                    Unit (96 tests ✅)                        │
│  EmailFactory, Conditions, ProxyRotator, utils,             │
│  crawler parallelism + driver lifecycle (mocked)            │
└─────────────────────────────────────────────────────────────┘
```

The unit tests already cover the bulk of the logic. E2E is valuable mainly as a pre-flight check before a real campaign run — not as part of a CI pipeline.
