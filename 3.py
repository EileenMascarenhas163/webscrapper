import asyncio
import os
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy

async def final_stable_deep_crawl(start_url, keyword, output_dir="llm_ready_data"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 1. Setup Strategy
    # Using BFS to get breadth then depth
    bfs_strategy = BFSDeepCrawlStrategy(
        max_depth=1, 
        include_external=False, 
        max_pages=20
    )

    # 2. Setup Config with STREAMING enabled
    # stream=True is the key to bypassing the 'list' object bug
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        deep_crawl_strategy=bfs_strategy,
        stream=True, 
        wait_for="body"
    )

    async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
        print(f"🚀 Starting Deep Stream Crawl: {start_url}")
        
        match_count = 0
        
        # 3. Use 'async for' to process results one-by-one
        # This replaces arun_many and handles the result stream correctly
        async for result in await crawler.arun(url=start_url, config=run_config):
            
            # Filter by your keyword
            if keyword.lower() in result.url.lower():
                if result.success:
                    match_count += 1
                    
                    # Create unique folder for this specific sub-route
                    folder_id = result.url.split("=")[-1] if "=" in result.url else str(match_count)
                    page_path = os.path.join(output_dir, f"match_{folder_id}")
                    os.makedirs(page_path, exist_ok=True)

                    # Extract Markdown string safely
                    md_content = result.markdown
                    if hasattr(result.markdown, 'raw_markdown'):
                        md_content = result.markdown.raw_markdown

                    # Save the LLM data
                    with open(os.path.join(page_path, "content.md"), "w", encoding="utf-8") as f:
                        f.write(f"--- SOURCE: {result.url} ---\n\n{md_content}")
                    
                    with open(os.path.join(page_path, "source.html"), "w", encoding="utf-8") as f:
                        f.write(result.cleaned_html or result.html)

                    print(f"✅ [{match_count}] Saved: {result.url}")
                else:
                    print(f"⚠️ Failed to crawl {result.url}: {result.error_message}")

    print(f"\n✨ Success! Total matched sub-routes saved: {match_count}")

if __name__ == "__main__":
    # Example: match 'item' to get HN discussion pages
    asyncio.run(final_stable_deep_crawl("https://www.merck.com/products/", "news"))