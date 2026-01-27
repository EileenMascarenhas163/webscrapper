import asyncio
import json
import pandas as pd
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

async def main():
    # 1. Setup global browser config
    browser_cfg = BrowserConfig(headless=True)
    
    # 2. Define the schema once
    new_schema = {
        "name": "news",
        "baseSelector": "article.o-search-result-product",
        "fields": [
           # {"name": "title", "selector": "h2", "type": "text"},
            {"name": "link", "selector": "h2.h3", "type": "text"}
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
     # Updated JS code for scrolling and waiting
            js_scroll_and_load = """
            async () => {
                const scrollDelay = 3000; // Time to wait for new content (ms)
                let lastHeight = document.body.scrollHeight;
                
                while (true) {
                    // Scroll to the bottom
                    window.scrollTo(0, document.body.scrollHeight);
                    
                    // Wait for potential network activity/rendering
                    await new Promise(resolve => setTimeout(resolve, scrollDelay));
                    
                    // Check if new content was loaded
                    let newHeight = document.body.scrollHeight;
                    if (newHeight === lastHeight) {
                        break; // No more content loaded
                    }
                    lastHeight = newHeight;
                }
            };
            """
            config = CrawlerRunConfig(
                session_id=session_id,
                extraction_strategy=extraction_strategy,
                js_code=js_scroll_and_load if page_count > 1 else None,
                # Wait for the next set of results to load after clicking
                wait_for="css:div.o-search-result-product",
                cache_mode=CacheMode.BYPASS
            )

            result = await crawler.arun(
                url="https://www.nouryon.com/product-search/",
                config=config
            )

            if result.success:
                data = json.loads(result.extracted_content)
                
                # Check if we got new data; if the page didn't change, stop.
                if not data or (all_news and data[0]['link'] == all_news[-1]['link']):
                    print("No more new content or reached the end.")
                    break
                
                all_news.extend(data)
                #print(json.dumps(data,indent=2))
                print(f"Extracted {len(data)} items from page {page_count}.")
                page_count += 1
                
                # Optional: limit pages to avoid infinite loops during testing
                if page_count > 1: break 
            else:
                print(f"Failed to crawl page {page_count}: {result.error_message}")
                break

    if all_news:
        df = pd.DataFrame(all_news)
        # Drop duplicates in case the crawler grabbed the same page twice
        #df = df.drop_duplicates(subset=['link'])
        
        file_name = "nouryon.xlsx"
        df.to_excel(file_name, index=False)
        print(f"\nFinished! Total unique links saved: {len(df)}")
    else:
        print("No data was collected.")
    print(f"Total items collected: {len(all_news)}")

if __name__ == "__main__":
    asyncio.run(main())