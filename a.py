import yaml
import os
import time
import requests
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, TimeoutError

OUTPUT_DIR = "downloaded_pdfs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def is_allowed(url, suffixes):
    netloc = urlparse(url).netloc.lower()
    return any(netloc.endswith(s) for s in suffixes)

def download_pdf(url, site_name, downloaded):
    if url in downloaded:
        return

    try:
        response = requests.get(url, timeout=30)
    except Exception:
        return

    if "application/pdf" not in response.headers.get("Content-Type", "").lower():
        return

    filename = url.split("/")[-1].replace(" ", "_")
    path = os.path.join(OUTPUT_DIR, f"{site_name}_{filename}")

    with open(path, "wb") as f:
        f.write(response.content)

    downloaded.add(url)
    print(f"Downloaded: {path}")

def handle_pagination(page, pagination_cfg):
    if pagination_cfg["type"] == "click":
        try:
            next_btn = page.locator(pagination_cfg["next_selector"])
            if next_btn.count() == 0:
                return False
            next_btn.first.click()
            page.wait_for_timeout(1500)
            return True
        except TimeoutError:
            return False

    if pagination_cfg["type"] == "scroll":
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(pagination_cfg.get("scroll_wait", 2))
        return True

    return False  # type == none

def run():
    with open("sites.yaml", "r") as f:
        sites = yaml.safe_load(f)["sites"]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        for site in sites:
            name = site["name"]
            suffixes = site["allowed_domain_suffixes"]
            selector = site["pdf_selector"]
            pagination = site.get("pagination", {"type": "none"})
            downloaded = set()

            for url in site["page_urls"]:
                print(f"\nProcessing site: {name}")
                print(f"Opening: {url}")

                page.goto(url, wait_until="domcontentloaded", timeout=60000)

                try:
                    page.wait_for_selector(selector, timeout=60000)
                except TimeoutError:
                    print("❌ No PDF links found on page")
                    continue

                page_number = 1

                while True:
                    print(f"📄 Page {page_number}")

                    links = page.eval_on_selector_all(
                        selector,
                        "els => els.map(e => e.href)"
                    )

                    for link in links:
                        if link.lower().endswith(".pdf") and is_allowed(link, suffixes):
                            download_pdf(link, name, downloaded)

                    if not handle_pagination(page, pagination):
                        print("✅ Pagination finished")
                        break

                    page_number += 1

        browser.close()

if __name__ == "__main__":
    run()
