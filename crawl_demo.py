import asyncio
import json
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

async def main():
    # 1. Setup global browser config
    browser_cfg = BrowserConfig(headless=True)
    
    # 2. Define the schema once
    new_schema = {
        "name": "news",
        "baseSelector": "div.sds-searchResult",
        "fields": [
            {"name": "title", "selector": "h2", "type": "text"},
            {"name": "link", "selector": "a.sds-downloadBtn", "type": "attribute", "attribute": "href"}
        ]
    }
    
    extraction_strategy = JsonCssExtractionStrategy(schema=new_schema)
    session_id = "ecolab_pagination_session"
    all_news = []
    page_count = 1

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        while True:
            print(f"--- Scraping Page {page_count} ---")
            
            # For the first page, we just visit the URL. 
            # For subsequent pages, we execute the JS click and wait for content.
            js_next = "const btn = document.querySelector('a.sds-pgli-item-arrow.sds-frontArrow-item'); if(btn) btn.click();"
            
            config = CrawlerRunConfig(
                session_id=session_id,
                extraction_strategy=extraction_strategy,
                js_code=js_next if page_count > 1 else None,
                # Wait for the next set of results to load after clicking
                wait_for="css:div.sds-searchResult",
                cache_mode=CacheMode.BYPASS
            )

            result = await crawler.arun(
                url="https://www.ecolab.com/sds-search?languageCode=English",
                config=config
            )

            if result.success:
                data = json.loads(result.extracted_content)
                
                # Check if we got new data; if the page didn't change, stop.
                if not data or (all_news and data[0]['title'] == all_news[-1]['title']):
                    print("No more new content or reached the end.")
                    break
                
                all_news.extend(data)
                print(json.dumps(data,indent=2))
                print(f"Extracted {len(data)} items from page {page_count}.")
                page_count += 1
                
                # Optional: limit pages to avoid infinite loops during testing
                if page_count > 3: break 
            else:
                print(f"Failed to crawl page {page_count}: {result.error_message}")
                break

    print(f"Total items collected: {len(all_news)}")

if __name__ == "__main__":
    asyncio.run(main())