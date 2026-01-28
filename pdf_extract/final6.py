from pathlib import Path
import json
from PyPDF2 import PdfReader
import re

# --- Configuration ---
input_folder = "./input_pdfs" 
output_file = "sds_section_1_only.json"

def extract_section_one(raw_text, file_link):
    # 1. Clean up "Noise"
    cleaned_text = re.sub(r'\d{6,}\s*-\d{2}.*?\d{2}\.\d{2}\.\d{4}.*?(\d\s/\s\d)', '', raw_text)
    
    # 2. Split by SECTION keyword - STRICT MATCH for "1"
    # \b1\b ensures we only match the number 1, not 11, 12, or 13.
    sections = re.split(r'(SECTION\s+\b1\b[\.\:]?)', cleaned_text, flags=re.IGNORECASE)
    
    result = {}
    
    # 3. Process the split sections
    # If the split worked, the header is at index 1 and content at index 2
    if len(sections) > 1:
        header = sections[1].strip()
        content = sections[2].strip()
        
        # We need to stop "content" before the next section starts
        # Split the content by any "SECTION [Number]" to keep only the body of Section 1
        body_parts = re.split(r'SECTION\s+\d+', content, flags=re.IGNORECASE)
        clean_content = body_parts[0].strip()
        
        # Clean up whitespace
        clean_content = re.sub(r'\s+', ' ', clean_content).strip()
        
        result["SECTION_1"] = {
            "title": header,
            "body": clean_content,
            "pdf_link": file_link
        }
            
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
