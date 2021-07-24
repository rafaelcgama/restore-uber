<h1 style="text-align: center;"> <span><b>Operation Restore Uber Account</b></span></h1>
<h4 style="text-align: center;"> <span><b>Disclaimer: this crawler was operational as of 05/18/2020</b></span></h4>




![](/images/uber_disabled.jpeg)


<h2 style="text-align: center;"> <span><i>Objective</i></span></h2>

The goal of this project is to create a crawler to scrap LinkedIn for all Uber employees in San Francisco and São Paulo and mass email them a letter hoping that someone, somewhere would be customer oriented enough to reactivate my account.



<h2 style="text-align: center;"> <span><i>Background</i></span></h2>

The idea for this project emerged when my Uber account was disabled, and after a long time trying to restore it, I became very frustrated and finally gave up trying fix it via customer service. If you are interested in knowing the whole story you should read the [email](uber.txt) I sent them. Long story short, my account started to get blocked for no reason. Every time I would reach their customer service and they would always say that it was just a glitch and would promptly reactivate it. This went on and on until one day, without any explanation, they permanently disabled my account and stop responding me.

At this point, the smart move would have been to just change my phone number and get a new account. But after going through all the headache and having spent a lot of time emailing them back and forth, I refused to bow, and instead, had the "brilliant idea" to spend even <ins>more of my time</ins> on this issue and came up with this project.



<h2 style="text-align: center;"> <span><i>Dataset</i></span></h2>

Uber doesn't really have a catalog or an API I could just pull their employees emails from so I had to get the data myself. I noticed by exchanging emails with Uber that their emails had two different formats, as shown in the example below:


Rafael Gama
```text
rafael@uber.com
```
```text
rafaelg@uber.com
```

Now I that knew Uber's email formats, all I needed was to get a list of employees first and last names and construct the emails. In order to do that, I developed a [crawler](crawler/crawler_linkedin.py) that goes to LinkedIn's people search section, selects a city and a company, and scrape all results.



<h2 style="text-align: center;"><span><i>Crawler Development</i></span></h2>

LinkedIn proved to be a worthy adversary and a particularly hard site to crawl. After analyzing the task, I came up with the following set challenges and solutions:

* #### LinkedIn requires JavaScript to render content on the page:
    I am familiar with both [selenium](https://selenium-python.readthedocs.io/) and [requests](https://requests.readthedocs.io/en/master/) but because of this peculiarity, I couldn't crawl the website using requests so I had to settle for **selenium**

* #### LinkedIn server reject a large series of requests from the same IP address in a given time period and suspends your ability to search for a few days. Also, the page rendering time would greatly vary between requests:
    To avoid using long sleep times, I tried to use Selenium's Wait module to dynamically wait for the page to load but had little success. The code was unstable and breaking all the time so I was forced to increase the sleep times to solve both problems.

* #### LinkedIn is on the lookout for bot behavior patterns:
    To reduce my chances of being flagged, I created and applied a set of functions that try to simulate human behavior by scrolling up and down and randomly clicking on profiles.



<h2 style="text-align: center;"><span><i>Data Preparation</i></span></h2>

Number of results in each city:

* [San Francisco](/data_collected/san_francisco.json): 940
* [São Paulo](/data_collected/sao_paulo.json): 1000

However, not all results were relevant for my purposes as many of my results no longer work at Uber among other things. So I went on to the process of [cleaning and exploring](notebooks/data_cleaning.ipynb) my dataset to come up with a more relevant employee list that would increase my chances of being helped while saving resources. Because the dataset is not complex, there wasn't much to do so I wrote a little [script](data_cleaning/data_cleaning.py) to execute the following actions:

* **Search and remove duplicates**
* **Remove all employees not currently employed at Uber**
* **Remove all employees showing "LinkedIn Member" as a name**
* **Remove all employees working in the capacity of a driver/motorista (Portuguese)**
* **Remove all employees working for Uber Eats and Uber Freight, UberAir, UberAIR / UberElevate and Uber Works**

After cleaning the data, I was left with 764 employees (779 using [pandas](https://pandas.pydata.org/)) from San Francisco and 585 employees for São Paulo (692 using pandas). The discrepancy between the results using my script and pandas got me a little intrigued but I decided to investigate that at a later time. Then, my next step was to develop an [email constructor](email_factory/email_factory.py) that returns 2 emails per name, one in each format.



<h2 style="text-align: center;"><span><i>Execution</i></span></h2>

Finally, all that was left to do was to integrate the email constructor in the [email sender script](email_sender/email_sender.py) and start bombarding Uber with emails, right?

Awwww, if it was only that easy...There is still one challenge left to overcome: Servers restrictions at both ends.

* **Both servers can flag my emails as spam**
* **LinkedIn's server may perceive my emails as a security threat**
* **My provider (Gmail) has [email sending limits](https://support.google.com/a/answer/166852?hl=en) of their own**

Because the content of my emails is exactly the same aside the person being addressed, they are in considerable risk of being flagged as spam. At the same time, if the emailing frequency is too high, it may trigger a security alert. The million dollar question is, how much is too much? Because I am not a expert in servers, I decided to be cautious and **randomly space out** the time between emails and send them in **batches of 20 emails** every **10 minutes**, until I hit **360 sent emails**, which was target I stipulated per day.


<h2 style="text-align: center;"><span><i>Results</i></span></h2>

The outcome of the project couldn't have been better. I ended up getting my account restored in the very first round of emails!!! 

In the end, 168 emails were sent but only 31 reached its destination. I was expecting the conversion rate to be twice of that because I was only using 2 email formats per employee. After further investigation, I discovered that Uber uses a few other email [formats](https://rocketreach.co/uber-email-format_b5ddab60f42e55aa) so that explains why most of them were not delivered.

So that's it! Mission accomplished!!! My account is back in business so let's see if will remais this way now...   


<h2 style="text-align: center;"><span><i>Potential Improvements</i></span></h2>

Since this is a pet project, the first and foremost goal was to have it up a running as fast as possible so I could actually try to fix my problem and **restore my Uber account**. However, while I and I was working on the project, I had many ideas on what can be done to improve the crawler's performance, scalability and robustness. These are a few of those ideas:

* **Find a way to reduce the number and duration of sleep times**
* **Parallelize code in order to run multiple collections simultaneously**
* **Rotate between different IPs to reduce the chance of getting flagged**
* **Find out the reason for the discrepancy between the results generated by using my data cleaning function and pandas.**
* **Refactor code to use a workflow management system, to become more robust to failures and be able to resume pipelines from failing points**
