from apscheduler.schedulers.blocking import BlockingScheduler
from runner import run_site

sites = [
    "https://www.ecolab.com/sds-search?languageCode=English"
]

scheduler = BlockingScheduler()

@scheduler.scheduled_job("interval", hours=24)
def crawl_all():
    for site in sites:
        run_site(site)

scheduler.start()
