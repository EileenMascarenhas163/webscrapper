import asyncio
from crawl4ai import AsyncWebCrawler
import json
async def get_dropdown_values():
    async with AsyncWebCrawler() as crawler:
        # Define your script
        extraction_js = """
        const data = {
            brands: Array.from(document.querySelectorAll('select[name="ctl00$MainContentHolder$DocLibViewer$ddlBrands"]  > option')).map(opt => ({text: opt.innerText, value: opt.value})),
            countries: Array.from(document.querySelectorAll('select[name="ctl00$MainContentHolder$DocLibViewer$ddlCountry"] > option ')).map(opt => ({text: opt.innerText, value: opt.value}))
        };
        console.log(data)
        return data;
        """
        
        # Pass the script into the arun method directly
        result = await crawler.arun(
            url="https://msds.deco.akzonobel.com",
            js_code=extraction_js,
            wait_for="select[name='ctl00$MainContentHolder$DocLibViewer$ddlBrands']" # Ensures the dropdown is loaded before running JS
        )
        
        # The result of your JS is stored in result.js_execution_result
        if result.success:
                # result.js_execution_result contains the dictionary returned by your JS
            data = result.js_execution_result
            
            # Print as clean, formatted JSON
            print(data)
        else:
            print(f"Error: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(get_dropdown_values())