import yaml
import os
import requests
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright, TimeoutError

OUTPUT_DIR = "downloaded_pdfs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def download_file(url, filename):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            with open(os.path.join(OUTPUT_DIR, filename), "wb") as f:
                f.write(response.content)
            return True
    except Exception as e:
        print(f"      Error: {e}")
    return False

def handle_pagination(page, pagination_cfg, current_page_num):
    selector = pagination_cfg.get("next_selector")
    if not selector or selector == "none":
        return False

    try:
        # 1. Identify the 'Next' button
        next_btn = page.locator(selector).first
        if next_btn.count() == 0 or not next_btn.is_visible():
            print("🏁 No visible 'Next' button found.")
            return False

        # 2. CAPTURE STATE: Get the first PDF link to detect page change
        first_pdf = page.locator("a.sds-downloadBtn").first
        old_link = first_pdf.get_attribute("href") if first_pdf.count() > 0 else ""

        print(f"➡️ Clicking Next (moving away from Page {current_page_num})...")
        
        # 3. Perform the click via JavaScript
        next_btn.scroll_into_view_if_needed()
        page.evaluate(f"document.querySelector('{selector}').click()")

        # 4. WAIT FOR DATA TO CHANGE (Fixed Syntax)
        try:
            # We pass old_link as an argument to the JS function to avoid f-string issues
            page.wait_for_function(
                "old => document.querySelector('a.sds-downloadBtn') && document.querySelector('a.sds-downloadBtn').getAttribute('href') !== old",
                arg=old_link,
                timeout=15000
            )
            print(f"✅ Page {current_page_num + 1} loaded.")
            page.wait_for_timeout(2000) 
            return True
        except Exception:
            print("⚠️ Data did not change. You might be on the last page.")
            return False

    except Exception as e:
        print(f"      Pagination error: {e}")
        return False

def run():
    if not os.path.exists("sites.yaml"):
        print("Error: sites.yaml not found.")
        return

    with open("sites.yaml", "r") as f:
        config = yaml.safe_load(f)
        sites = config["sites"]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        for site in sites:
            name = site["name"]
            pdf_selector = site["pdf_selector"]
            pagination_cfg = site.get("pagination", {})
            
            for url in site["page_urls"]:
                print(f"\n--- Site: {name} ---")
                page.goto(url, wait_until="load")
                
                current_page = 1
                while True:
                    print(f"📄 Processing Page {current_page}")
                    
                    page.wait_for_selector(pdf_selector, timeout=20000)
                    page.wait_for_timeout(1000) 

                    buttons = page.locator(pdf_selector)
                    count = buttons.count()
                    for i in range(count):
                        btn = buttons.nth(i)
                        btn.scroll_into_view_if_needed()
                        link = btn.get_attribute("href")
                        
                        if link and link != "#":
                            full_url = urljoin(page.url, link)
                            filename = f"{name}_p{current_page}_{i+1}.pdf"
                            if download_file(full_url, filename):
                                print(f"  [+] Saved: {filename}")

                    if not handle_pagination(page, pagination_cfg, current_page):
                        break
                    
                    current_page += 1

        browser.close()

if __name__ == "__main__":
    run()