
import pandas as pd
import requests
import os

EXCEL_FILE = "merck_usa_sds1.xlsx"     # your Excel file
COLUMN_NAME = "links"         # column containing URLs
DOWNLOAD_DIR = "merck_download"    # local folder

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Read Excel
df = pd.read_excel(EXCEL_FILE, engine="openpyxl")

for index, url in df[COLUMN_NAME].items():
    if pd.isna(url):
        continue

    url = str(url).strip()
    print(f"Downloading row {index}: {url}")

    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()

        filename = os.path.basename(url.split("?")[0])
        if not filename:
            filename = f"file_{index}"

        filepath = os.path.join(DOWNLOAD_DIR, filename)

        with open(filepath, "wb") as f:
            f.write(response.content)

        print(f"Saved to {filepath}")

    except Exception as e:
        print(f"Failed: {e}")
