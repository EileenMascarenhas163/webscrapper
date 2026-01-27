
# sds_extract_gemini.py
import os
import json
import time
from pathlib import Path
from typing import Dict, Any, List

import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from PyPDF2 import PdfReader

# ---------------- CONFIG ----------------
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")  # or "gemini-1.5-flash" for lower cost
INPUT_DIR = Path("input_pdfs")           # folder that contains your SDS PDFs
OUTPUT_XLSX = Path("sds_output.xlsx")
MAX_CHARS_PER_CHUNK = 12000              # chunk size for long PDFs
DO_OCR_IF_IMAGE_ONLY = False             # set True if SDS are scanned images and tesseract installed

# SDS-specific schema (ONLY what you asked)
SCHEMA: Dict[str, str] = {
    "product_name": "string",
    "country": "string",
    "region": "string (e.g., regulatory region like 'US/OSHA', 'EU/CLP', or subnational region/state/province if present)",
    "manufacturer_name": "string"
}
# ---------------- END CONFIG ----------------


# ----------- OCR helpers (optional) -----------
def pdf_to_text_with_ocr(pdf_path: Path) -> str:
    try:
        from pdf2image import convert_from_path
        import pytesseract
        from PIL import Image  # noqa: F401
    except ImportError:
        raise RuntimeError("OCR requested but pdf2image/pytesseract/Pillow not installed.")
    pages = convert_from_path(str(pdf_path), dpi=300)
    texts = []
    for img in pages:
        txt = pytesseract.image_to_string(img)
        texts.append(txt)
    return "\n\n".join(texts)


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Try embedded text; if empty and OCR enabled, run OCR."""
    try:
        reader = PdfReader(str(pdf_path))
        texts = []
        for page in reader.pages:
            t = page.extract_text() or ""
            texts.append(t)
        combined = "\n\n".join(texts).strip()
        if combined:
            return combined
        if DO_OCR_IF_IMAGE_ONLY:
            return pdf_to_text_with_ocr(pdf_path)
        return ""
    except Exception:
        if DO_OCR_IF_IMAGE_ONLY:
            return pdf_to_text_with_ocr(pdf_path)
        raise


# ----------- Utilities -----------
def chunk_text(s: str, max_chars: int) -> List[str]:
    s = s.strip()
    if len(s) <= max_chars:
        return [s]
    chunks = []
    start = 0
    while start < len(s):
        end = min(start + max_chars, len(s))
        split = s.rfind("\n\n", start, end)
        if split == -1 or split <= start + max_chars * 0.6:
            split = end
        chunks.append(s[start:split])
        start = split
    return chunks


def build_system_prompt(schema: Dict[str, str]) -> str:
    fields = [f'  "{k}": {v}' for k, v in schema.items()]
    fields_str = "{\n" + ",\n".join(fields) + "\n}"
    return (
        "You are an SDS (Safety Data Sheet) information extraction engine.\n"
        "Return ONLY valid JSON that exactly matches the requested schema and types.\n"
        "If a field is not present, use null (for strings). Do not add extra keys.\n"
        "Do not include comments or explanations.\n\n"
        "Extraction guidance (SDS-specific):\n"
        "- product_name: Prefer 'Product identifier' from Section 1 or title header.\n"
        "- manufacturer_name: Prefer the entity labeled 'Manufacturer', 'Supplier', or 'Responsible party'.\n"
        "- country: Use the explicitly stated country associated with the manufacturer/supplier address block.\n"
        "- region: If a regulatory region is explicitly stated (e.g., 'US/OSHA', 'EU/CLP', 'Canada/WHMIS'), return that.\n"
        "         Else if a subnational region (state/province) is present in the address, return that.\n"
        "         Otherwise return null.\n\n"
        f"Schema:\n{fields_str}"
    )


def build_user_prompt(chunk_text: str) -> str:
    return (
        "Extract the fields as per the schema from the following SDS text.\n"
        "If uncertain, return null rather than guessing.\n\n"
        f"Document text:\n---\n{chunk_text}\n---"
    )


def make_hyperlink_cell(file_path: Path) -> str:
    uri = file_path.resolve().as_uri()  # file:///C:/... link
    return f'=HYPERLINK("{uri}", "Open PDF")'


def merge_partial_records(partials: List[Dict[str, Any]], schema: Dict[str, str]) -> Dict[str, Any]:
    """For scalars, take the first non-null/non-empty value across chunks."""
    result: Dict[str, Any] = {k: None for k in schema.keys()}
    for p in partials:
        for k in schema.keys():
            v = p.get(k, None)
            if result[k] in (None, "") and v not in (None, ""):
                result[k] = v
    return result


def flatten_for_excel(record: Dict[str, Any]) -> Dict[str, Any]:
    # All fields are scalars in this use case
    return dict(record)


# ----------- Gemini client -----------
def get_gemini_model():
    import google.generativeai as genai
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set in environment.")
    genai.configure(api_key=api_key)

    generation_config = {
        "temperature": 0.0,
        "top_p": 0.0,
        "top_k": 1,
        "response_mime_type": "application/json",  # aim for pure JSON
    }
    model = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        generation_config=generation_config,
    )
    return model


@retry(
    reraise=True,
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=20),
    retry=retry_if_exception_type(Exception),
)
def call_gemini_json(model, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
    """Call Gemini and parse JSON; fallback to extracting the largest JSON block."""
    prompt = f"{system_prompt}\n\n{user_prompt}"
    resp = model.generate_content(prompt, request_options={"timeout": 90})
    text = (resp.text or "").strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = text[start:end + 1]
            return json.loads(candidate)
        raise


# ----------- Main flow -----------
def main():
    INPUT_DIR.mkdir(exist_ok=True)
    pdf_files = sorted([p for p in INPUT_DIR.glob("*.pdf") if p.is_file()])
    if not pdf_files:
        print(f"No PDFs found in {INPUT_DIR}. Place files there and re-run.")
        return

    model = get_gemini_model()
    system_prompt = build_system_prompt(SCHEMA)

    rows = []
    for pdf in pdf_files:
        print(f"Processing: {pdf.name}")
        text = extract_text_from_pdf(pdf)
        if not text:
            print(f"  Warning: No text extracted from {pdf.name}. (OCR={'ON' if DO_OCR_IF_IMAGE_ONLY else 'OFF'})")

        chunks = chunk_text(text, MAX_CHARS_PER_CHUNK) if text else [""]

        partials: List[Dict[str, Any]] = []
        for i, ch in enumerate(chunks, 1):
            user_prompt = build_user_prompt(ch)
            try:
                result = call_gemini_json(model, system_prompt, user_prompt)
                # Keep only schema keys, defaulting to null
                clean = {k: result.get(k, None) for k in SCHEMA.keys()}
                partials.append(clean)
            except Exception as e:
                print(f"  Gemini error on chunk {i}/{len(chunks)}: {e}")
                continue
            time.sleep(0.2)  # mild pacing to avoid rate limits

        merged = merge_partial_records(partials, SCHEMA) if partials else {k: None for k in SCHEMA.keys()}

        flat = flatten_for_excel(merged)
        flat["pdf_file_name"] = pdf.name
        flat["pdf_path_link"] = make_hyperlink_cell(pdf)
        rows.append(flat)

    # Order columns and write Excel
    all_cols = list(SCHEMA.keys()) + ["pdf_file_name", "pdf_path_link"]
    df = pd.DataFrame(rows)
    for col in all_cols:
        if col not in df.columns:
            df[col] = None
    df = df[all_cols]

    with pd.ExcelWriter(OUTPUT_XLSX, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="sds_extracted", index=False)

    print(f"Done. Wrote {OUTPUT_XLSX.resolve()}")


if __name__ == "__main__":
    main()
