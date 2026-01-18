# tools.py
import os
import asyncio
from pydantic import BaseModel, Field
#from praisonai_tools import BaseTool

from crawl4ai import AsyncWebCrawler, LLMConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy


class ModelFee(BaseModel):
    llm_model_name: str = Field(..., description="Name of the model.")
    input_fee: str = Field(..., description="Fee for input token for the model.")
    output_fee: str = Field(..., description="Fee for output token for the model.")


class ModelFeeTool(BaseTool):
    name: str = "ModelFeeTool"
    description: str = "Extracts model fees for input and output tokens from the given pricing page."

    def _run(self, url: str):
        return asyncio.run(self._async_run(url))

    async def _async_run(self, url: str):
        llm_config = LLMConfig(
            provider="openai/gpt-4o",
            api_token=os.getenv("OPENAI_API_KEY")
        )

        extraction_strategy = LLMExtractionStrategy(
            llm_config=llm_config,
            schema=ModelFee.model_json_schema(),
            extraction_type="schema_list",   # ⭐ important
            instruction="""
            From the crawled content, extract ALL mentioned model names
            along with their input and output token fees.
            Do not miss any models.
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

            return result.extracted_content


if __name__ == "__main__":
    tool = ModelFeeTool()
    url = "https://openai.com/api/pricing/"
    result = tool.run(url)
    print(result)
