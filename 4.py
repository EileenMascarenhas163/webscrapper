import asyncio
import os
import json
from pydantic import BaseModel, Field
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, LLMConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer

class PageSummary(BaseModel):
    title: str = Field(..., description="Title of the article")
    relevance_score: int = Field(..., description="Score 1-10")
    summary: str = Field(..., description="Short summary")

async def smart_rank_and_scrape(start_url, goal_keywords, goal_description):
    # Set your API Key here or in .env
    # os.environ["OPENAI_API_KEY"] = "sk-..."

    scorer = KeywordRelevanceScorer(keywords=goal_keywords, weight=0.5)
    strategy = BestFirstCrawlingStrategy(
        max_depth=1,
        max_pages=8, # Keep it small to test
        url_scorer=scorer,
        include_external=False
    )

    llm_config = LLMConfig(
        provider="gemini-2.5-flash-lite", 
        api_token=os.getenv("OPENAI_API_KEY")
    )

    extraction_strategy = LLMExtractionStrategy(
        llm_config=llm_config,
        schema=PageSummary.model_json_schema(),
        instruction=f"Evaluate based on: {goal_description}. Give a score 1-10."
    )

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        extraction_strategy=extraction_strategy,
        cache_mode=CacheMode.BYPASS,
        stream=True  # Important to process results one-by-one
    )

    async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
        print(f"🎯 Goal: {goal_description}")
        
        best_match = None
        highest_score = -1

        try:
            # We await the arun call which returns an async generator
            result_gen = await crawler.arun(url=start_url, config=run_config)
            
            async for result in result_gen:
                if result.success and result.extracted_content:
                    try:
                        # --- FIX 1: Handle List vs Dict error ---
                        data = json.loads(result.extracted_content)
                        # If the LLM returned a list [{}], take the first item
                        if isinstance(data, list) and len(data) > 0:
                            data = data[0]
                        
                        current_score = data.get("relevance_score", 0)
                        print(f"🔍 Scanned: {result.url} | AI Score: {current_score}")

                        if current_score > highest_score:
                            highest_score = current_score
                            best_match = {"url": result.url, "data": data, "markdown": result.markdown}
                            
                    except Exception as e:
                        print(f"⚠️ Failed to parse AI response: {e}")
        
        except Exception as e:
            # --- FIX 2: Catch the "Context" internal bug ---
            print(f"⚠️ Internal Crawl4AI context error caught: {e}")

        # 6. Save the Winner
        if best_match:
            print(f"\n🏆 WINNER: {best_match['url']} ({highest_score}/10)")
            with open("winner_content.md", "w", encoding="utf-8") as f:
                f.write(f"# {best_match['data'].get('title')}\nURL: {best_match['url']}\n\n")
                f.write(best_match['markdown'])
            print("✨ Saved to winner_content.md")
        else:
            print("❌ No high-quality matches found.")


if __name__ == "__main__":
    asyncio.run(smart_rank_and_scrape(
        start_url="https://news.ycombinator.com",
        goal_keywords=["GPU", "CPU", "automation", "news"],
        goal_description="Find the most in-depth discussion about GPU, CPU , and automation ."
    ))