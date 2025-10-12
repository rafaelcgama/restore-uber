# Operation Restore Uber Account

> **Disclaimer:** This crawler was operational as of **05/18/2020**.
> Built purely as a personal experiment — not affiliated with Uber or LinkedIn.

<div align="center">
  <img src="/images/uber_disabled.jpeg" width="400">
</div>

---

## Objective

The goal of this project was to build a crawler to scrape LinkedIn for all Uber employees located in **San Francisco** and **São Paulo**, and then **mass-email** them a letter — hoping that someone, somewhere, would be customer-oriented enough to help reactivate my Uber account.

---

## Background

This project was born out of frustration. After my Uber account was repeatedly blocked without explanation — and after enduring multiple back-and-forths with customer support who called it a "glitch" every time — my account was suddenly **permanently disabled**.

Uber stopped responding. No warnings, no explanations.

Now, the rational move would’ve been to just create a new account with a different phone number. But after everything, I refused to give in. Instead, I had the "brilliant idea" to pour even **more time and energy** into a technical workaround… and this is the result.

If you want the full story, check out the [email I sent them](uber.txt).

---

## Dataset Construction

Uber doesn’t offer an API or public employee directory. But based on prior emails exchanged with Uber, I noticed two common email formats:

**Example: John Doe**

john@uber.com

johnd@uber.com

With this pattern in hand, all I needed was a list of employees’ names. I created a [crawler](crawler/crawler_linkedin.py) that performs a LinkedIn search by city and company, then scrapes the list of employee profiles.

---

## Crawler Development

Crawling LinkedIn is a small war of attrition. Here’s what went wrong — and how I duct-taped it into working:

- **JavaScript Rendering:**  
  LinkedIn loads everything dynamically, so static scraping with requests was useless.
I switched to Selenium, which could at least *pretend* to be human.

- **Rate Limiting & Bans:**  
  Hit LinkedIn too fast and you’re done.
  I tried clever dynamic waits with WebDriverWait, but reliability tanked — so I surrendered to long, static sleep() calls. Crude, but effective.


- **Anti-Bot Detection:**  
  To look less like a bot, I made the crawler behave more like an impatient intern — random scrolling, unpredictable pauses, and the occasional useless click.

  It wasn’t elegant. But it survived long enough to get the data.

---

## 🧼 Data Preparation

Raw results by city:

- [San Francisco](/data_collected/san_francisco.json): 940
- [São Paulo](/data_collected/sao_paulo.json): 1000

Of course, most of that was noise — ex-employees, recruiters, and “LinkedIn Members” with no visible name.
So I ran a custom [data cleaning script](data_cleaning/data_cleaning.py) to refine the dataset and discard irrelevant entries.

The result: fewer rows, more signal, and slightly less chaos — a cleaner, sharper list of people actually worth emailing.

### Cleaning Steps:

- Remove duplicates
- Exclude ex-Uber employees
- Remove profiles with the name “LinkedIn Member”
- Filter out drivers and operations roles (e.g., Uber Eats, Uber Freight, Uber Works, Uber Air/Elevate)

**Final cleaned counts:**

| City          | My Script | Pandas |
|---------------|-----------|--------|
| San Francisco | 764       | 779    |
| São Paulo     | 585       | 692    |

The discrepancy between my script and Pandas intrigued me - but that's a mystery for another day

Next, I built an [email constructor](email_factory/email_factory.py) to generate two possible address formats per employee. One of them had to hit someone’s inbox.

---

## Execution Strategy

Once the emails were ready, I fed them into the [email sender script](email_sender/email_sender.py).
At that point, it should’ve been as simple as hitting “Send.”, right?!

Not quite yet...

---

### Emailing Constraints:

- **Spam Filters:** Identical bulk messages are spam-filter bait — change too little, and you’re flagged instantly.
- **Gmail Limits:** Gmail enforces strict daily caps; see [Gmail’s sending limits](https://support.google.com/a/answer/166852?hl=en).
- **Security Flags:** oo much “unusual activity” and Google starts thinking you’re a bot — or worse, a marketer.

---

### My Strategy:

- Send in **batches of 20 emails**
- Introduce **random time delays**
- Cap at **360 emails per day**

This approach added just enough randomness to dodge spam filters while staying safely under Gmail’s radar.

---

## Results

**Success.**  
My account was reactivated after the **first batch** of emails.

## Stats:

I expected better delivery rates, but later discovered Uber uses multiple email formats beyond the two I implemented. See this [reference](https://rocketreach.co/uber-email-format_b5ddab60f42e55aa) for more variations.

---

## Potential Improvements

This was a quick, impulsive hack that somehow evolved into a working system. If I ever revisited it, here’s how I’d make it smarter, faster, and far more sustainable:

- Replace brute-force sleeps with smart waits:
Use explicit Selenium conditions or event hooks to make the scraper reactive instead of time-dependent.
(“Sleep(5)” may work, but it’s the duct tape of automation.)

- Parallelize the crawler:
Split LinkedIn searches by city or alphabet range and run them concurrently using threads or asyncio. Faster collection, same headache.

- Add proxy rotation:
Implement rotating IPs, headers, and user agents to distribute requests and reduce detection risk.


- Audit data cleaning logic:
The mismatch between my script and Pandas still bugs me. Proper unit tests or a deterministic cleaning pipeline would fix that.

- Introduce workflow orchestration:
A lightweight orchestrator like Prefect, Luigi, or Airflow would let the process recover from partial failures and make it reproducible — not just “Raff’s cursed cron job that somehow works.”

---

## Final Thoughts

What started as a small act of stubbornness turned into a full-blown automation pipeline.
It was unnecessary, slightly obsessive, and definitely not the most efficient solution — but it worked.

My Uber account is back.
Let’s see how long it stays that way!