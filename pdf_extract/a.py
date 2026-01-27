import os
import json
import time
import random
import pandas as pd
from PyPDF2 import PdfReader
from google import genai
from google.genai import types

# --- CONFIGURATION ---
client = genai.Client(api_key="AIzaSyAcW5nNe0cte_83DuSEw_TbA0bCu7weTWY")
folder_path = "./input_pdfs"  # Path to your PDFs
output_excel = "SDS_Extraction_Master.xlsx"

def extract_dense_chunk(pdf_path):
    """Extracts only the first page and removes noise to keep the input layer small."""
    try:
        reader = PdfReader(pdf_path)
        # 99% of identifying info is on Page 1
        page_text = reader.pages[0].extract_text()
        
        # Keep only the first 60 lines to minimize token usage
        lines = page_text.split('\n')[:60]
        # Remove empty lines or very short fragments
        clean_lines = [line.strip() for line in lines if len(line.strip()) > 3]
        
        return "\n".join(clean_lines)
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        return ""

def get_structured_data(text):
    """Sends a small text chunk to Gemini with Exponential Backoff for Rate Limits."""
    if not text.strip():
        return {"product_name": "Empty/Scanned", "country": "N/A", "manufacturer_name": "N/A"}

    schema = {
        "type": "OBJECT",
        "properties": {
            "product_name": {"type": "STRING"},
            "country": {"type": "STRING"},
            "manufacturer_name": {"type": "STRING"},
        },
        "required": ["product_name", "country", "manufacturer_name"],
    }

    # Retry settings
    max_retries = 5
    base_delay = 5  # Start with 5 seconds

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash", 
                contents=f"Extract JSON: product_name, country, manufacturer_name from this SDS:\n{text}",
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema
                )
            )
            return json.loads(response.text)

        except Exception as e:
            if "429" in str(e):
                # Exponential backoff: 5s, 10s, 20s, 40s...
                delay = (base_delay * (2 ** attempt)) + random.uniform(0, 1)
                print(f"Rate limit (429) hit. Waiting {delay:.1f}s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(delay)
            else:
                print(f"Permanent Error: {e}")
                break

    return {"product_name": "Quota Failed", "country": "N/A", "manufacturer_name": "N/A"}

def run():
    if not os.path.exists(folder_path):
        print(f"Error: Folder '{folder_path}' not found.")
        return

    all_data = []
    files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
    print(f"Processing {len(files)} files...")

    for filename in files:
        print(f"\n--- Current File: {filename} ---")
        full_path = os.path.abspath(os.path.join(folder_path, filename))
        
        # Step 1: Extract a dense, small chunk to save tokens
        small_chunk = extract_dense_chunk(full_path)
        
        # Step 2: Get data with retry logic
        extracted = get_structured_data(small_chunk)
        
        # Step 3: Add path and save
        extracted['pdf_link'] = full_path
        all_data.append(extracted)
        
        # Safety gap for Free Tier: Wait 3 seconds between every file
        time.sleep(3)

    # Step 4: Final Excel Export
    df = pd.DataFrame(all_data)
    with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='SDS_Data')
        worksheet = writer.sheets['SDS_Data']
        link_col = df.columns.get_loc("pdf_link")
        for row_num, path in enumerate(df['pdf_link']):
            worksheet.write_url(row_num + 1, link_col, f'file:///{path}', string='Open PDF')

    print(f"\nDone! File created: {output_excel}")

if __name__ == "__main__":
    run()