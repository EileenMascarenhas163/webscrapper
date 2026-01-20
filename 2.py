import asyncio
import os
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy 

async def display_matched_markdown(start_url, keyword):
    # 1. Setup Strategy
    bfs_strategy = BFSDeepCrawlStrategy(
        max_depth=1, 
        include_external=False, 
        max_pages=20
    )

    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        deep_crawl_strategy=bfs_strategy,
        wait_for="body"
    )

    async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
        print(f"🚀 Crawling {start_url}... (Bug-fix mode enabled)")
        
        # This is where the 'list' error usually starts
        raw_results = await crawler.arun_many(urls=[start_url], config=run_config)

        print(f"\n--- MATCHED SUB-ROUTES FOR: '{keyword}' ---")
        
        for item in raw_results:
            # FIX: If 'item' is a list (the bug), get the first actual result object inside it
            if isinstance(item, list):
                if len(item) > 0:
                    result = item[0]
                else:
                    continue
            else:
                result = item

            # Now we can safely check for the keyword and status
            if keyword.lower() in result.url.lower():
                if result.success:
                    print(f"\n✅ MATCHED: {result.url}")
                    
                    # Safe access to Markdown content
                    md_text = ""
                    if hasattr(result.markdown, 'raw_markdown'):
                        md_text = result.markdown.raw_markdown
                    else:
                        md_text = str(result.markdown)

                    print("-" * 40)
                    print(md_text[:1000] + "\n... [Remaining content hidden] ...")
                    print("-" * 40)
                else:
                    # If it's still failing, it's a real site error, not a code crash
                    print(f"❌ Site Error on {result.url}: {result.error_message}")

if __name__ == "__main__":
    # Example: match 'item' to get Hacker News threads
    asyncio.run(display_matched_markdown("https://news.ycombinator.com", "news"))