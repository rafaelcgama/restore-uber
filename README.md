# Operation Restore Uber Account

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![Selenium](https://img.shields.io/badge/Selenium-4.18-43B02A?logo=selenium&logoColor=white)
![Prefect](https://img.shields.io/badge/Prefect-3.6-024DFD?logo=prefect&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-103%20passing-brightgreen?logo=pytest&logoColor=white)
![Status](https://img.shields.io/badge/Status-Educational%20Archive-lightgrey)

> **Disclaimer:** This crawler was operational as of **05/18/2020**.
> Built purely as a personal experiment — not affiliated with Uber or LinkedIn.

<div align="center">
  <img src="images/uber_disabled.jpeg" width="400" alt="Uber account disabled screen">
</div>

---

## The Problem

My Uber account was permanently disabled without warning, explanation, or appeal. After multiple rounds with customer support who kept calling it a "glitch," Uber went silent.

The straightforward fix would have been a new account. Instead, I built this.

If you want the full story, the [email I sent Uber employees](uber.txt) says it all.

---

## The Solution

A purpose-built automation pipeline that:

1. **Crawls LinkedIn** for Uber employees in San Francisco and São Paulo
2. **Constructs email addresses** using known Uber email format patterns
3. **Sends personalised emails** in rate-limited batches to avoid spam filters

**It worked.** Account reactivated after the first batch.

---

## Architecture

![Architecture Diagram](images/architecture.png)

---

## How It Works

### Step 1 — Data Collection

Uber has no public employee directory. Based on existing Uber email correspondence, two common formats were identified for an employee named **John Doe**:

```
john@uber.com
johnd@uber.com
```

The [LinkedIn crawler](crawler/crawler_linkedin.py) searches for Uber employees by city, scraping names and job titles. Both cities run **simultaneously** via threads — cutting total crawl time roughly in half.

| City          | Raw Records |
|---------------|-------------|
| San Francisco | 940         |
| São Paulo     | 1000        |

### Step 2 — Data Cleaning

Raw results contain noise: ex-employees, recruiters, drivers, and anonymous "LinkedIn Member" placeholders. The [cleaning script](data_cleaning/data_cleaning.py) filters all of that out.

**Filters applied:**
- Remove "LinkedIn Member" placeholders
- Exclude ex-Uber employees
- Remove drivers and non-corporate roles (Uber Air, Freight, Elevate)
- Strip duplicates

| City          | After Cleaning |
|---------------|----------------|
| San Francisco | 764            |
| São Paulo     | 585            |

### Step 3 — Email Construction

The [email factory](email_factory/email_factory.py) generates up to **six address formats** per employee:

| Format | Example |
|--------|---------|
| First only | `john@uber.com` |
| Last only | `doe@uber.com` |
| First + last | `johndoe@uber.com` |
| First + last initial | `johnd@uber.com` |
| Last + first initial | `doej@uber.com` |
| First initial + last | `jdoe@uber.com` |

### Step 4 — Sending

The [email sender](email_sender/email_sender.py) dispatches in configurable batches with randomised delays to stay under Gmail's rate limits and avoid spam detection.

| Setting | Default |
|---------|---------|
| Batch size | 20 emails |
| Delay between batches | 15 minutes |
| Daily cap | 360 emails |

---

## Crawler Engineering

LinkedIn is actively hostile to automation. Three layers of countermeasures are in place:

### Anti-Bot Detection
- **`undetected-chromedriver`** — patches `navigator.webdriver = true` at the browser level, bypassing LinkedIn's JS fingerprinting
- **User-Agent rotation** — every session gets a randomised, realistic Chrome UA via `fake-useragent`
- **Proxy rotation** — proxies are fetched automatically from the [ProxyScrape](https://proxyscrape.com) free API on startup. Override with a private pool via `PROXY_LIST`, or swap the source entirely via `PROXY_SOURCE_URL`
- **Human-like behaviour** — random scrolling, unpredictable pauses, and occasional profile visits

### Rate Limiting
- Static `sleep()` calls used deliberately over smart waits — more reliable under real-world LinkedIn behaviour
- Random delays between page navigations (6–10 seconds)
- Periodic longer pauses every 10 pages

---

## Improvements Made (**March 6th, 2026**)

This project evolved from a one-off hack into a production-grade pipeline. Here's what was added:

### ⚡ Parallel Crawling
Both cities now run simultaneously using `ThreadPoolExecutor` — each in its own isolated Chrome process with no shared state. The city-level `_crawl_city()` function is designed to fail independently: if one city errors out, the other's results are still preserved.

### 🛡️ Anti-Detection Stack
Three-layer evasion built into the base crawler via `ProxyRotator` — automatically applied to every session without changes to crawling logic.

### 🎛️ Prefect Orchestration
The full pipeline is now a proper Prefect workflow (`pipeline/flow.py`):
- Each stage (`crawl → clean → send`) is an independent `@task` with automatic retries
- Crawl failures retry up to 3× before propagating — clean and send are never re-run unnecessarily
- Replaces the cron job: `pipeline.serve(cron="0 6 * * *")`
- Optional dashboard: `prefect server start` → http://localhost:4200

### 🧪 Test Suite
103 unit tests across 5 modules — all run offline, no browser or network required. See [`docs/e2e_testing.md`](docs/e2e_testing.md) for end-to-end testing strategies.

---

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure credentials
cp .env.example .env && nano .env

# 3. Run the full Prefect-orchestrated pipeline
python main.py

# — or run each stage individually —
python crawler/crawler_linkedin.py
python data_cleaning/data_cleaning.py
python email_sender/email_sender.py

# — or run directly via the flow module —
python -m pipeline.flow
```

> **Note:** `undetected-chromedriver` automatically downloads a matching ChromeDriver — no manual installation needed. You only need **Google Chrome** (or a [Chrome for Testing](https://googlechromelabs.github.io/chrome-for-testing/) build) installed on your machine.

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `USERNAME_LINKEDIN` | ✅ | LinkedIn login email |
| `PASSWORD_LINKEDIN` | ✅ | LinkedIn password |
| `USERNAME_EMAIL` | ✅ | Gmail address for sending |
| `PASSWORD_EMAIL` | ✅ | Gmail App Password |
| `DELAY` | ✗ | Seconds between email batches (default: 900) |
| `BATCH_SIZE` | ✗ | Emails per batch (default: 20) |
| `EMAIL_TARGET` | ✗ | Max emails per run (default: 360) |
| `PROXY_LIST` | ✗ | Comma-separated private proxies — overrides the free API pool |
| `PROXY_SOURCE_URL` | ✗ | Free proxy API URL (default: ProxyScrape elite HTTP proxies) |
| `CHROME_BINARY` | ✗ | Path to a [Chrome for Testing](https://googlechromelabs.github.io/chrome-for-testing/) binary |

### Running Tests

103 unit tests across 5 modules — all run offline (no browser, no network).

```bash
# Run all unit tests
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=. --cov-report=term-missing

# Run only E2E tests (requires live LinkedIn credentials)
pytest tests/e2e/ -m e2e -v
```

For end-to-end testing strategies (sandboxed LinkedIn account, mock SMTP, Prefect flow integration), see [`docs/e2e_testing.md`](docs/e2e_testing.md).

---

## Project Structure

```
restore-uber/
├── crawler/
│   ├── __init__.py
│   ├── crawler_base.py           # Abstract base (DriverFunctions + ProxyRotator)
│   └── crawler_linkedin.py       # LinkedIn scraper with parallel city crawling
├── data_cleaning/
│   ├── __init__.py
│   └── data_cleaning.py          # Filters raw scrape output
├── email_factory/
│   ├── __init__.py
│   └── email_factory.py          # Generates 6 email format variants per name
├── email_sender/
│   ├── __init__.py
│   └── email_sender.py           # SMTP dispatch with batching & rate limiting
├── pipeline/
│   ├── __init__.py
│   └── flow.py                   # Prefect workflow (crawl → clean → send)
├── utils/
│   ├── __init__.py
│   ├── driver_functions.py       # undetected-chromedriver helpers + CHROME_BINARY support
│   ├── proxy_rotator.py          # Proxy + User-Agent rotation (free API or PROXY_LIST)
│   └── utils.py                  # File I/O, logging, path helpers
├── tests/
│   ├── __init__.py
│   ├── test_proxy_rotator.py
│   ├── test_email_factory.py
│   ├── test_data_cleaning.py
│   ├── test_utils.py
│   └── test_crawler_linkedin.py  # Crawler logic (mocked driver, no browser)
├── docs/
│   └── e2e_testing.md            # E2E testing strategies & manual protocol
├── images/
│   └── architecture.png          # Pipeline architecture diagram
├── notebooks/                    # Exploratory Jupyter notebooks
├── data_raw/                     # Raw crawler output (JSON)
├── data_cleaned/                 # Cleaned output (JSON)
├── main.py                       # Entry point → delegates to pipeline/flow.py
├── requirements.txt
├── .env.example                  # Template for required environment variables
├── Dockerfile
└── .gitignore
```

---

## Results

**Account reactivated after the first batch of emails.**

A few weeks of engineering time to avoid making a new account. Worth it? Objectively, no. But what started as a stubborn act of defiance turned into a genuinely interesting system — one that taught more about browser automation, anti-bot evasion, email deliverability, and pipeline orchestration than most contrived side projects do.

The account is still active as of **March 6, 2026**. Let's see how long that lasts.
