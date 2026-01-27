from pathlib import Path
import json
from PyPDF2 import PdfReader
import re

# --- Configuration ---
input_folder = "./input_pdfs" 
output_file = "sds_section_1_only.json"

def extract_section_one(raw_text, file_link):
    # 1. Clean up "Noise" (Ecolab specific footers/dates)
    cleaned_text = re.sub(r'\d{6,}\s*-\d{2}.*?\d{2}\.\d{2}\.\d{4}.*?(\d\s/\s\d)', '', raw_text)
    
    # 2. Split by SECTION keyword - Handles "SECTION 1.", "SECTION 1:", "SECTION 1  "
    # This regex looks for 'SECTION', then space, then digits, then an optional punctuation
    sections = re.split(r'(SECTION\s+\d+[\.\:]?)', cleaned_text, flags=re.IGNORECASE)
    
    result = {}
    
    # 3. Look for the first section specifically
    for i in range(1, len(sections), 2):
        header = sections[i].strip()
        # Look for "SECTION 1" in the header string
        if re.search(r'SECTION\s+1', header, re.IGNORECASE):
            content = sections[i+1].strip() if i+1 < len(sections) else ""
            # Clean up whitespace and newlines
            clean_content = re.sub(r'\s+', ' ', content).strip()
            
            result["SECTION_1"] = {
                "title": header,
                "body": clean_content,
                "pdf_link": file_link
            }
            break # We only want Section 1, so stop here
            
    return result

# --- Main Processing Loop ---
master_data = {}
pdf_folder = Path(input_folder)

# Check if folder exists
if not pdf_folder.exists():
    print(f"Error: Folder '{input_folder}' not found.")
else:
    for pdf_file in pdf_folder.glob("*.pdf"):
        print(f"Processing: {pdf_file.name}")
        
        file_path = pdf_file.resolve()
        file_link = f"file:///{file_path.as_posix()}"
        
        try:
            reader = PdfReader(str(pdf_file))
            sds_text = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    sds_text += text
            
            # If no text was extracted at all, it might be a scanned image
            if not sds_text.strip():
                print(f"  [!] No text found in {pdf_file.name}. (Might be a scanned image)")
                master_data[pdf_file.name] = {}
                continue

            # Process the text
            section_data = extract_section_one(sds_text, file_link)
            
            if section_data:
                master_data[pdf_file.name] = section_data
                print(f"  [✓] Successfully extracted Section 1")
            else:
                master_data[pdf_file.name] = {}
                print(f"  [!] Found text, but could not identify 'SECTION 1' pattern.")

        except Exception as e:
            print(f"  [X] Error reading {pdf_file.name}: {e}")
            master_data[pdf_file.name] = {}

# --- Final Save ---
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(master_data, f, indent=4)

print(f"\nProcess complete. Data saved to {output_file}")