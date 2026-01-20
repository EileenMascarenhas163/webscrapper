from graph import agent
from browser import browser
from time import sleep

def run_site(url, retries=3):
    browser.open(url)
    for i in range(retries):
        try:
            result = agent.invoke({"url": url})
            return result
        except Exception as e:
            print("Retry:", e)
            sleep(5)
    print("❌ Failed site:", url)
