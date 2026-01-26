import pandas as pd
import requests
import os
import time
import re

# --- CONFIGURATION ---
EXCEL_FILE = "merck_usa_sds1.xlsx"
COLUMN_NAME = "Links"
DOWNLOAD_DIR = "downloads"

# 1. Headers to look like a real browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def clean_filename(name):
    """Removes characters that are illegal in Windows filenames."""
    return re.sub(r'[\\/*?:"<>|]', "_", name)

# Read Excel
try:
    df = pd.read_excel(EXCEL_FILE, engine="openpyxl")
    print(f"Successfully loaded {len(df)} rows from Excel.")
except Exception as e:
    print(f"Error reading Excel: {e}")
    exit()

# --- MAIN DOWNLOAD LOOP ---
for index, url in df[COLUMN_NAME].items():
    if pd.isna(url):
        continue

    url = str(url).strip()
    
    # Generate a unique name using the row index to prevent overwriting
    # zfill(3) turns "1" into "001" for better sorting
    row_id = str(index + 1).zfill(3)
    
    # Extract filename and remove URL parameters (everything after ?)
    base_name = os.path.basename(url.split("?")[0])
    if not base_name:
        base_name = "document.pdf"
    
    # Combine ID and cleaned name
    filename = f"{row_id}_{clean_filename(base_name)}"
    filepath = os.path.join(DOWNLOAD_DIR, filename)

    print(f"[{row_id}] Attempting: {url}")

    try:
        # 2. Use 'stream=True' to handle large files better
        response = requests.get(url, headers=HEADERS, timeout=30, stream=True)
        response.raise_for_status()

        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        print(f"   ✅ Saved as: {filename}")
        
        # 3. Short pause to avoid hitting rate limits
        time.sleep(0.5)

    except requests.exceptions.HTTPError as e:
        print(f"   ❌ HTTP Error: {e.response.status_code} for row {index+1}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

print("\n--- Process Complete ---")
print(f"Check the '{DOWNLOAD_DIR}' folder. You should now see unique IDs on every file.")