import asyncio
import json
import pandas as pd
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

async def main():
    browser_cfg = BrowserConfig(headless=True)
    
    # Updated Schema to filter for USA - English specifically
    new_schema = {
        "name": "merck_sds_usa",
        "baseSelector": "div.b6-accordion-list-item", 
        "fields": [
          
            {
                "name": "usa_english_link", 
                # Targets the link where the title attribute contains 'USA - English'
                "selector": 'a[title*="USA - English"]', 
                "type": "attribute", 
                "attribute": "href"
            }
        ]
    }
    
    extraction_strategy = JsonCssExtractionStrategy(schema=new_schema)

    # JavaScript to open accordions so the DOM is fully rendered
    js_open_accordions = """
    document.querySelectorAll('details.b6-accordion-list-item-details').forEach(details => {
        details.open = true;
    });
    """

    config = CrawlerRunConfig(
        extraction_strategy=extraction_strategy,
        js_code=js_open_accordions,
        wait_for="css:div.b6-accordion-list-item", 
        cache_mode=CacheMode.BYPASS,
       
    )

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun(
            url="https://www.merck.com/products/safety-data-sheets/?type=hh-item",
            config=config
        )

        if result.success:
            raw_data = json.loads(result.extracted_content)
            
            # Filter results: Only keep items that actually found a USA link
            final_data = [item for item in raw_data if item.get('usa_english_link')]
            
            print(f"Successfully found {len(final_data)} USA-English products.")
            
            if final_data:
                df = pd.DataFrame(final_data)
                df.to_excel("merck_usa_sds1.xlsx", index=False)
                print("Results saved to merck_usa_sds.xlsx")
        else:
            print(f"Error during crawl: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(main())