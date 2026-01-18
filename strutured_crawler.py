import os
import asyncio
from pydantic import BaseModel, Field
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from crawl4ai import LLMConfig



class OpenAIModelFee(BaseModel):
    model_name: str = Field(..., description="Name of the OpenAI model.")
    input_fee: str = Field(..., description="Fee for input token for the OpenAI model.")
    output_fee: str = Field(..., description="Fee for output token for the OpenAI model.")


async def main():
    url = "https://openai.com/api/pricing/"
    llm_config = LLMConfig(
        provider="openai/gpt-4o",
        api_token=os.getenv("OPENAI_API_KEY")
    )

    extraction_strategy = LLMExtractionStrategy(
        llm_config=llm_config,
        schema=OpenAIModelFee.model_json_schema(),
        extraction_type="schema_list",
        instruction="""
        From the crawled content, extract ALL OpenAI model names
        along with their input and output token fees.
        Return a list of objects.
        """
    )

    async with AsyncWebCrawler(
        browser_type="chromium",
        headless=True
    ) as crawler:

        result = await crawler.arun(
            url,
            word_count_threshold=1,
            extraction_strategy=extraction_strategy,
            bypass_cache=True
        )

        print(result.)
        print("--------------------------------")
        


if __name__ == "__main__":
    asyncio.run(main())


