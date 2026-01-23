

#pip install "crawl4ai @ git+https://github.com/unclecode/crawl4ai.git" transformers torch nltk pydantic pandas openpyxl
#python -m playwright install chromium


import asyncio
import json
import pandas as pd
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

async def main():
    browser_cfg = BrowserConfig(headless=True)
    
    new_schema = {
        "name": "news",
        "baseSelector": "div.sds-searchResult",
        "fields": [
            {"name": "link", "selector": "a.sds-downloadBtn", "type": "attribute", "attribute": "href"}
        ]
    }
    
    extraction_strategy = JsonCssExtractionStrategy(schema=new_schema)
    session_id = "ecolab_pagination_session"
    all_news = []
    page_count = 1
    max_pages = 3  # Set this to the total number of pages you want

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        while page_count <= max_pages:
            print(f"--- Scraping Page {page_count} ---")
            
            # JavaScript to click the next button and scroll it into view
            js_next = """
            const btn = document.querySelector('a.sds-pgli-item-arrow.sds-frontArrow-item');
            if(btn) {
                btn.scrollIntoView();
                btn.click();
            }
            """
            
            config = CrawlerRunConfig(
                session_id=session_id,
                extraction_strategy=extraction_strategy,
                js_code=js_next if page_count > 1 else None,
                wait_for="css:div.sds-searchResult",
                cache_mode=CacheMode.BYPASS
            )

            result = await crawler.arun(
                url="https://www.ecolab.com/sds-search?languageCode=English",
                config=config
            )

            if result.success:
                # Add a small delay to ensure the DOM has updated after the click
                if page_count > 1:
                    await asyncio.sleep(2) 
                
                data = json.loads(result.extracted_content)
                
                if not data:
                    print("No data found on this page. Ending.")
                    break

                # Append only new links
                all_news.extend(data)
                print(f"Page {page_count}: Extracted {len(data)} links.")
                
                page_count += 1
            else:
                print(f"Error on page {page_count}: {result.error_message}")
                break

    # Final Export
    if all_news:
        df = pd.DataFrame(all_news)
        # Drop duplicates in case the crawler grabbed the same page twice
        df = df.drop_duplicates(subset=['link'])
        
        file_name = "ecolab_links.xlsx"
        df.to_excel(file_name, index=False)
        print(f"\nFinished! Total unique links saved: {len(df)}")
    else:
        print("No data was collected.")

if __name__ == "__main__":
    asyncio.run(main())