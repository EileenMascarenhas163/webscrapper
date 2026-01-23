main file ==== crawl_demo.py
demo.png
ecolab_link






pip install "crawl4ai @ git+https://github.com/unclecode/crawl4ai.git" transformers torch nltk pydantic
python -m playwright install chromium


pip install crawl4ai langgraph pydantic langchain-openai
crawl4ai-setup



pip install langgraph langchain openai pydantic crawl4ai playwright apscheduler python-dotenv



1 -> get the crawler
2 -> get the deep crawling behavious and match the context and get all the matched subroute
3 -> give the scrape data
4-> 3 rd LLM strategy 



curl -X POST 'https://api.firecrawl.dev/v2/agent' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer your-api-key' \
  -d @- <<'EOF'
{
  "prompt": "Extract all Safety Data Sheet (SDS) PDF links from ecolab.com. Include data for all available regions and languages. For each SDS, capture the product name and the direct link to the PDF file.",
  "schema": {
    "type": "object",
    "properties": {
      "ecolab_sds_documents": {
        "type": "array",
        "description": "List of Safety Data Sheet (SDS) documents from ecolab.com",
        "items": {
          "type": "object",
          "properties": {
            "product_name": {
              "type": "string",
              "description": "Name of the product"
            },
            "product_name_citation": {
              "type": "string",
              "description": "Source URL for product_name"
            },
            "region": {
              "type": "string",
              "description": "Region for which the SDS is available"
            },
            "region_citation": {
              "type": "string",
              "description": "Source URL for region"
            },
            "language": {
              "type": "string",
              "description": "Language of the SDS document"
            },
            "language_citation": {
              "type": "string",
              "description": "Source URL for language"
            },
            "pdf_link": {
              "type": "string",
              "description": "Direct link to the SDS PDF file"
            },
            "pdf_link_citation": {
              "type": "string",
              "description": "Source URL for pdf_link"
            }
          },
          "required": [
            "product_name",
            "pdf_link"
          ]
        }
      }
    },
    "required": [
      "ecolab_sds_documents"
    ]
  },
  "urls": ["https://www.ecolab.com"],
  "model": "spark-1-mini"
}
EOF

from firecrawl import FirecrawlApp
from pydantic import BaseModel, Field
from typing import List, Optional

app = FirecrawlApp(api_key = "your-api-key")

class ExtractSchema(BaseModel):
    ecolab_sds_documents: List[dict] = Field(..., description="List of Safety Data Sheet (SDS) documents from ecolab.com")

result = app.agent(
    schema=ExtractSchema,
    prompt="Extract all Safety Data Sheet (SDS) PDF links from ecolab.com. Include data for all available regions and languages. For each SDS, capture the product name and the direct link to the PDF file.",
    urls = ["https://www.ecolab.com"],
    model = "spark-1-mini",
)   


import Firecrawl from '@mendable/firecrawl-js';
import { z } from 'zod';

const firecrawl = new Firecrawl({ apiKey: 'your-api-key' });

const result = await firecrawl.agent({
  prompt: "Extract all Safety Data Sheet (SDS) PDF links from ecolab.com. Include data for all available regions and languages. For each SDS, capture the product name and the direct link to the PDF file.",
  schema: z.object({
      ecolab_sds_documents: z.array(z.object({
        product_name: z.string().describe("Name of the product"),
        product_name_citation: z.string().describe("Source URL for product_name").optional(),
        region: z.string().describe("Region for which the SDS is available").optional(),
        region_citation: z.string().describe("Source URL for region").optional(),
        language: z.string().describe("Language of the SDS document").optional(),
        language_citation: z.string().describe("Source URL for language").optional(),
        pdf_link: z.string().describe("Direct link to the SDS PDF file"),
        pdf_link_citation: z.string().describe("Source URL for pdf_link").optional()
      })).describe("List of Safety Data Sheet (SDS) documents from ecolab.com")
    }),
  urls: ["https://www.ecolab.com"],
  model: 'spark-1-mini',
});