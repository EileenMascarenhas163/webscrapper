from playwright.sync_api import sync_playwright
import time

class Browser:
    def __init__(self):
        self.pw = sync_playwright().start()
        self.browser = self.pw.chromium.launch(headless=False)
        self.page = self.browser.new_page()

    def open(self, url):
        self.page.goto(url, timeout=60000)
        time.sleep(3)

    def click(self, text):
        self.page.get_by_text(text, exact=False).first.click()
        time.sleep(2)

    def paginate(self):
        self.page.get_by_text("Next", exact=False).first.click()
        time.sleep(2)

    def get_links(self):
        return [a.get_attribute("href")
                for a in self.page.query_selector_all("a")
                if a.get_attribute("href")]

    def close(self):
        self.browser.close()
        self.pw.stop()
