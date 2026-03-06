# Operation Restore Uber Account

![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
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
- **Proxy rotation** — disabled by default (`DISABLE_PROXY=true`) so local runs work cleanly from a residential IP. When running at scale from a cloud/datacenter IP, point `PROXY_LIST` at a paid service (Bright Data, Oxylabs, etc.) — the `ProxyRotator` will handle round-robin rotation automatically.
- **Human-like behaviour** — random scrolling, unpredictable pauses, and occasional profile visits

### Rate Limiting
- Static `sleep()` calls used deliberately over smart waits — more reliable under real-world LinkedIn behaviour
- Random delays between page navigations (6–10 seconds)
- Periodic longer pauses every 10 pages

---

## 2026 Revisit

When I finished this project in 2020 I noted several improvements I'd make if I were to do it again — proper orchestration, parallel crawling, containerisation, a test suite, cleaner logging. I never went back to it.

In March 2026 I used this repo as a hands-on exercise to learn **LLM agent-assisted development** (using Google DeepMind's Antigravity agent with Claude Sonnet 4.5 and Gemini 3 Pro). Rather than building something new, I applied those deferred improvements to a codebase I already understood well, which let me focus entirely on the tooling and workflow rather than the problem domain.

**What was added:**

- **Prefect orchestration** — `crawl → clean → send` as independent retried `@task`s with a shared `@flow`, replacing the original cron job
- **Parallel crawling** — both cities run simultaneously via `ThreadPoolExecutor`, each in an isolated Chrome process
- **Proxy rotation infrastructure** — `ProxyRotator` with round-robin rotation, User-Agent randomisation, and a `DISABLE_PROXY` toggle for local runs
- **Docker + Docker Compose** — reproducible environment with `.env`-based secret injection
- **103 unit tests** across 5 modules, all offline (no browser, no network)
- **Logging and configuration standardisation** — single `setup_logging()` entry point, module-level `getLogger(__name__)` throughout, centralised `.env` loading

**Why the crawler no longer runs:**
LinkedIn's search interface changed fundamentally after 2020. Company employees are now accessed via `/company/{name}/people/` with location filters and infinite scroll — a completely different interaction model from the paginated global People search the crawler was built against. Re-implementing the data collection layer (`_crawl_city()`) would have been a full rewrite with no additional learning value for this exercise, so it was left as-is. The pipeline, orchestration, data cleaning, email factory, and sending layers are all functional and unaffected.

The crawler is a snapshot of how LinkedIn worked in 2020. Everything around it reflects how I'd build it today.

---

## Setup

```bash
# 1. Install dependencies (requires Python 3.13)
pip install -r requirements.txt

# 2. Configure credentials
cp .env.example .env && nano .env

# 3. Run the full Prefect-orchestrated pipeline
python main.py

# — or use Docker Compose (Best Practice) —
docker-compose up --build

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
| `DELAY` | ✗ | Seconds between email batches (default: `900`) |
| `BATCH_SIZE` | ✗ | Emails per batch (default: `20`) |
| `EMAIL_TARGET` | ✗ | Max emails per run (default: `360`) |
| `DISABLE_PROXY` | ✗ | Set `true` to skip all proxy logic (default). Set `false` + add `PROXY_LIST` for paid proxies. |
| `PROXY_LIST` | ✗ | Comma-separated proxies from a paid service (e.g. `http://user:pass@host:port`). Requires `DISABLE_PROXY=false`. |
| `CHROME_BINARY` | ✗ | Path to a [Chrome for Testing](https://googlechromelabs.github.io/chrome-for-testing/) binary |
| `CHROME_PROFILE_DIR` | ✗ | Directory for a persistent Chrome profile. Set once, complete LinkedIn's email verification manually — all future runs reuse the saved session. **Local only** (see note below). |

> **LinkedIn session verification:** On a fresh Chrome session LinkedIn may send a 6-digit code to your email before allowing login. Setting `CHROME_PROFILE_DIR` saves the session cookie to disk so this only happens once. This workaround is **local-only** — Docker containers are ephemeral and have no GUI for the initial manual step, making fully automated verification impractical without additional IMAP integration.

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

For end-to-end testing strategies and current limitations, see [`docs/e2e_testing.md`](docs/e2e_testing.md).

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
│   ├── proxy_rotator.py          # Proxy + User-Agent rotation (opt-in via PROXY_LIST)
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
