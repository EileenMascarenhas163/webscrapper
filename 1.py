import asyncio
import os
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy 

async def comprehensive_deep_crawl(start_url, output_folder="full_site_crawl"):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 1. Strategy: Broad then Deep
    # max_depth=2: 
    # Level 0 (Home) -> Level 1 (All sub-routes) -> Level 2 (Links inside sub-routes)
    bfs_strategy = BFSDeepCrawlStrategy(
        max_depth=2, 
        include_external=False, # Stay on news.ycombinator.com
        max_pages=40            # Limit for safety; increase as needed
    )

    # 2. Run Configuration
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        deep_crawl_strategy=bfs_strategy,
        wait_for="body"
    )

    async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
        print(f"🚀 Starting broad & deep crawl: {start_url}")
        
        # arun_many returns a list of results after the crawl finishes
        results = await crawler.arun_many(
            urls=[start_url],
            config=run_config
        )

        for i, result in enumerate(results):
            if result.success:
                # Create a filename based on the URL or index
                # This ensures we save every sub-page found
                safe_url = result.url.replace("https://", "").replace("/", "_").replace("?", "_")[:80]
                filepath = os.path.join(output_folder, f"{i}_{safe_url}.md")
                
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(f"# URL: {result.url}\n\n")
                    f.write(result.markdown)
                
                print(f"✅ [{i}] Crawled: {result.url}")

if __name__ == "__main__":
    asyncio.run(comprehensive_deep_crawl("https://news.ycombinator.com"))