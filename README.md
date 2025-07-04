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

Crawling LinkedIn is no easy feat. Here were the core challenges and how I tackled them:

- **JavaScript Rendering:**  
  LinkedIn search results are rendered with JavaScript. So I used [Selenium](https://selenium-python.readthedocs.io/) instead of `requests`.

- **Rate Limiting & Bans:**  
  Too many requests from the same IP will get you blocked. I initially tried dynamic waits via `WebDriverWait`, but instability forced me to fallback to longer, static sleep intervals.

- **Anti-Bot Detection:**  
  To avoid detection, I added human-like behaviors — like scrolling, random delays, and occasional clicks.

---

## 🧼 Data Preparation

Raw results by city:

- [San Francisco](/data_collected/san_francisco.json): 940
- [São Paulo](/data_collected/sao_paulo.json): 1000

I then ran a custom [data cleaning script](data_cleaning/data_cleaning.py) to refine the dataset and discard irrelevant entries.

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

>The discrepancy between my script and Pandas intrigued me, but I saved it for another day.

Next, I created an [email constructor](email_factory/email_factory.py) to generate two address variants per employee.

---

## Execution Strategy

With the emails generated, I plugged them into the [email sender script](email_sender/email_sender.py).  
Now all I had to do was hit “send,” right?

Not quite…

### Emailing Constraints:

- **Spam Filters:** Bulk identical messages trigger spam detectors.
- **Gmail Limits:** See [Gmail’s sending limits](https://support.google.com/a/answer/166852?hl=en).
- **Security Flags:** Unusual activity might trigger account suspension.

### My Strategy:

- Send in **batches of 20 emails**
- Introduce **random time delays**
- Cap at **360 emails per day**

This approach helped avoid spam filters while keeping the process steady and under the radar.

---

## Results

**Success.**  
My account was reactivated after the **first batch** of emails.

### Stats:

- Emails sent: **168**
- Delivered: **31**
- Conversion: Account restored

I expected better delivery rates, but later discovered Uber uses multiple email formats beyond the two I implemented. See this [reference](https://rocketreach.co/uber-email-format_b5ddab60f42e55aa) for more variations.

---

## Potential Improvements

This was a fast-and-dirty pet project. But several ideas came to mind for making it more scalable and robust:

- Reduce `sleep()` time using smarter waits
- Parallelize scraping across threads or processes
- Use proxy rotation to bypass rate limits
- Investigate the data cleaning discrepancies
- Refactor to use a workflow manager (e.g. Airflow, Prefect) for recovery and modularity

---

## Final Thoughts

What began as a small act of stubbornness turned into a full-blown automation pipeline. It was a ridiculous workaround — but it worked. And now I have my Uber account back.

Let’s see if it stays that way.