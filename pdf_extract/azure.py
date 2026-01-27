import os
import json
import pandas as pd
from PyPDF2 import PdfReader
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

# --- CONFIGURATION ---
# Use the connection string from your Azure AI Foundry project overview
CONNECTION_STRING = "your_region.services.ai.azure.com/api/projects/your_project_id"
MODEL_DEPLOYMENT_NAME = "gpt-4o-mini" # The name you gave your model deployment
FOLDER_PATH = "./input_pdfs"
OUTPUT_EXCEL = "SDS_Extraction_Azure.xlsx"

# 1. Initialize Azure Client
# This uses your logged-in Azure account (az login) or environment variables
project_client = AIProjectClient.from_connection_string(
    connection_string=CONNECTION_STRING,
    credential=DefaultAzureCredential()
)

def extract_text_chunk(pdf_path):
    """Extracts first 2 pages for identification."""
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages[:2]:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        return ""

def get_structured_data_azure(text):
    """Uses Azure AI Foundry to extract structured JSON."""
    if not text.strip():
        return {"product_name": "Empty PDF", "country": "N/A", "manufacturer_name": "N/A"}

    # Structured prompt for Azure models
    prompt = (
        "You are a data extraction assistant. Extract the following fields from the SDS text: "
        "product_name, country, and manufacturer_name. "
        "Return the output strictly in valid JSON format."
    )

    try:
        # Get the chat client from the project
        chat_client = project_client.get_chat_completions_client()
        
        response = chat_client.complete(
            model=MODEL_DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"SDS Text:\n{text[:4000]}"} # Keeping input size safe
            ],
            response_format={"type": "json_object"} # Forces JSON mode
        )
        
        # Parse the JSON string from the Azure response
        content = response.choices[0].message.content
        return json.loads(content)
        
    except Exception as e:
        print(f"Azure API Error: {e}")
        return {"product_name": "Azure Error", "country": "N/A", "manufacturer_name": "N/A"}

def run():
    all_data = []
    files = [f for f in os.listdir(FOLDER_PATH) if f.lower().endswith('.pdf')]
    print(f"Starting Azure extraction for {len(files)} files...")

    for filename in files:
        print(f"Processing: {filename}")
        full_path = os.path.abspath(os.path.join(FOLDER_PATH, filename))
        
        raw_text = extract_text_chunk(full_path)
        extracted = get_structured_data_azure(raw_text)
        
        extracted['pdf_link'] = full_path
        all_data.append(extracted)

    # Export to Excel
    df = pd.DataFrame(all_data)
    with pd.ExcelWriter(OUTPUT_EXCEL, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Azure_SDS_Results')
        worksheet = writer.sheets['Azure_SDS_Results']
        link_col = df.columns.get_loc("pdf_link")
        for row_num, path in enumerate(df['pdf_link']):
            worksheet.write_url(row_num + 1, link_col, f'file:///{path}', string='Open PDF')

    print(f"Success! Master file created: {OUTPUT_EXCEL}")

if __name__ == "__main__":
    run()