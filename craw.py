import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig ,BrowserConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
import json
async def main():
    async with AsyncWebCrawler(config = BrowserConfig(headless=True)) as crawler:
        new_schema = {
            "name": "news",
           "baseSelector": "div.sds-searchResult", # The main row
        "fields": [
            {
                "name": "title",
                "selector": "div.sds-searchResult > h2",
                "type": "text"
            },
         
            {
                "name": "link",
                "selector": "a.sds-downloadBtn",
                "type": "attribute",
                "attribute": "href"
            },
           
        ]

        }

        results = await crawler.arun(
            url="https://www.ecolab.com/sds-search?languageCode=English",
            config=CrawlerRunConfig(extraction_strategy=JsonCssExtractionStrategy(schema=new_schema),session_id="hn_session")
        )

        news = []
        for result in results:
            if result.success:
                data = json.loads(result.extracted_content)
                news.extend(data)
                print(json.dumps(data,indent=2))
            else:
                print("failed")
        
        more_config = CrawlerRunConfig(
            js_code = "document.querySelector('a.sds-pgli-item-arrow.sds-frontArrow-item').click()",
            
            extraction_strategy = JsonCssExtractionStrategy(
                schema = new_schema
            ),
        )
        results = await crawler.arun(
            url="https://www.ecolab.com/sds-search?languageCode=English",
            config=more_config
        )
        for result in results:
            if result.success:
                data = json.loads(result.extracted_content)
                news.extend(data)
                print(json.dumps(data,indent=2))
            else:
                print("failed")

if __name__ == "__main__":
    asyncio.run(main())
