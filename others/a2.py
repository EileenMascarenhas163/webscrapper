import yaml
import os
import requests
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright, TimeoutError

OUTPUT_DIR = "downloaded_pdfs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def download_file(url, filename):
    """Downloads the file using requests with a browser-like header."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            with open(os.path.join(OUTPUT_DIR, filename), "wb") as f:
                f.write(response.content)
            return True
    except Exception as e:
        print(f"      Error saving file: {e}")
    return False

def run():
    if not os.path.exists("sites.yaml"):
        print("Error: sites.yaml not found.")
        return

    with open("sites.yaml", "r") as f:
        sites = yaml.safe_load(f)["sites"]

    with sync_playwright() as p:
        # headless=False is crucial so you can see the 'scrolling' action
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        for site in sites:
            name = site["name"]
            selector = site["pdf_selector"]
            
            for url in site["page_urls"]:
                print(f"\n--- Processing Site: {name} ---")
                page.goto(url, wait_until="load")
                
                # Initial wait for the table to exist
                try:
                    page.wait_for_selector(selector, timeout=20000)
                except TimeoutError:
                    print("❌ No download buttons found.")
                    continue

                # Get all button elements
                buttons = page.locator(selector)
                count = buttons.count()
                print(f"Found {count} results. Starting sequential download...")

                for i in range(count):
                    try:
                        # 1. Get the specific button and scroll to it
                        # This triggers the 'Lazy Load' so the link appears
                        btn = buttons.nth(i)
                        btn.scroll_into_view_if_needed()
                        page.wait_for_timeout(500) # Short pause for JS to update the link

                        # 2. Extract the link (href)
                        link = btn.get_attribute("href")
                        
                        if not link or link == "#":
                            # If no link, some sites require a hover to generate it
                            btn.hover()
                            page.wait_for_timeout(500)
                            link = btn.get_attribute("href")

                        if link:
                            full_url = urljoin(page.url, link)
                            # Generate a unique filename
                            clean_name = f"{name}_{i+1}.pdf"
                            
                            print(f"  [+] Downloading {i+1}/{count}: {full_url}")
                            
                            # 3. Use the download logic
                            if download_file(full_url, clean_name):
                                print(f"      ✅ Saved: {clean_name}")
                            else:
                                print(f"      ⚠️ Request failed for {clean_name}")
                        else:
                            print(f"      ❌ Could not find link for item {i+1}")

                    except Exception as e:
                        print(f"      ❌ Error on item {i+1}: {e}")
                    
                    # Small delay before moving to the next button
                    page.wait_for_timeout(1000)

        print("\n✨ Process finished.")
        browser.close()

if __name__ == "__main__":
    run()