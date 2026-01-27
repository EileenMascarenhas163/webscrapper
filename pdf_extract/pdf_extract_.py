
#pip install -U google-genai PyPDF2 pandas xlsxwriter
#pip install -q -U google-generativeai pandas xlsxwriter pymupdf
import google.generativeai as genai
import pandas as pd
import json
import os
import fitz  # PyMuPDF
# --- CONFIGURATION ---
genai.configure(api_key="AIzaSyDwbrd2bnLw6hDBpPUGr6g4zdM2HVls2cc")
folder_path = "./input_pdfs"
output_excel = "Master_SDS_List.xlsx"

def extract_text_from_pdf(pdf_path):
    text = ""
    with fitz.open(pdf_path) as doc:
        # Extracting first 2 pages is usually enough for these fields
        for page in doc[:2]: 
            text += page.get_text()
    return text

def get_gemini_extraction(text):
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Refined prompt for better accuracy
    prompt = f"""
    Analyze this Safety Data Sheet (SDS) text and extract exactly three fields.
    Return ONLY a valid JSON object with these keys: "product_name", "country", "manufacturer_name".
    
    Guidelines:
    - product_name: The full name of the chemical product.
    - country: The country where the company is located (e.g., Australia).
    - manufacturer_name: The name of the company/manufacturer.

    Text:
    {text}
    """
    
    try:
        response = model.generate_content(prompt)
        # Remove any markdown backticks if the model includes them
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except Exception as e:
        print(f"Extraction failed: {e}")
        return {"product_name": "Manual Check Req", "country": "N/A", "manufacturer_name": "N/A"}

def process_folder(path):
    all_results = []
    
    if not os.path.exists(path):
        print(f"Error: Folder '{path}' not found.")
        return

    for filename in os.listdir(path):
        if filename.lower().endswith(".pdf"):
            print(f"Processing: {filename}")
            full_path = os.path.join(path, filename)
            
            # 1. Get Text
            raw_text = extract_text_from_pdf(full_path)
            
            # 2. Extract Data
            data = get_gemini_extraction(raw_text)
            
            # 3. Add file info and path
            data['file_name'] = filename
            data['file_path'] = os.path.abspath(full_path)
            all_results.append(data)

    # 4. Save to Excel with Links
    if all_results:
        df = pd.DataFrame(all_results)
        # Reorder columns for better view
        cols = ["product_name", "country", "manufacturer_name", "file_path", "file_name"]
        df = df[cols]

        with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='SDS_Data')
            workbook = writer.book
            worksheet = writer.sheets['SDS_Data']
            
            # Create Hyperlinks in the 'file_path' column (index 3)
            for row_num, path in enumerate(df['file_path']):
                worksheet.write_url(row_num + 1, 3, f'file:///{path}', string='Open PDF')
        
        print(f"Done! Results saved to {output_excel}")

if __name__ == "__main__":
    process_folder(folder_path)