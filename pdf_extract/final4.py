from pathlib import Path
import json
from PyPDF2 import PdfReader
import re

file= "./input_pdfs/AU-EN-914474-CLEANTEC DRY LUBE.PDF"
file_path = Path(file).resolve()

file_link = f"file:///{file_path.as_posix()}"
print(file_link)
reader = PdfReader(file)
sds_text = " "
# Extract text from each page
for page in reader.pages:
    sds_text += page.extract_text()
    print(sds_text)


def chunk_sds_to_json(raw_text):
    # 1. Clean up "Noise" (Page numbers, dates, and repetitive footers)
    # This regex targets the specific Ecolab footer pattern you have
    cleaned_text = re.sub(r'\d{6,}\s*-\d{2}.*?\d{2}\.\d{2}\.\d{4}.*?(\d\s/\s\d)', '', raw_text)
    
    # 2. Split by SECTION keyword (flexible for different spacing/formatting)
    # This captures the section number and name
    sections = re.split(r'(SECTION\s+\d+\.)', cleaned_text)
    
    sds_json_data = {}
    
    # 3. Iterate and build the Dictionary
    for i in range(1, len(sections), 2):
        header = sections[i].strip()
        content = sections[i+1].strip() if i+1 < len(sections) else ""
        
        # Formatting for JSON/LLM
        # Replace multiple newlines with single spaces to keep it compact
        clean_content = re.sub(r'\s+', ' ', content).strip()
        
        # Create a clean Key (e.g., "SECTION_1")
        key_name = re.sub(r'[^A-Z0-9_]', '', header.replace(" ", "_").replace(".", ""))
        
        sds_json_data[key_name] = {
            "title": header,
            "body": clean_content
        }
    
    # 4. Convert dictionary to actual JSON string
    return json.dumps(sds_json_data, indent=4)

# Execute
json_output = chunk_sds_to_json(sds_text)
data = json.loads(json_output)
first_key = list(data.keys())[0]
first_value = data[first_key]
print(first_key)
first_value["pdf_link"] = file_link
print(first_value)