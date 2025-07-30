import streamlit as st
import cv2, re, json
import pytesseract
from pytesseract import Output
import numpy as np
from pdf2image import convert_from_bytes

# ---------------- Helper Functions ----------------

def extract_text_data(img):
    return pytesseract.image_to_data(img, output_type=Output.DICT)

def extract_invoice_fields(ocr_text):
    invoice_no = re.search(r"(?:Invoice\s*No\.?:?\s*)([A-Za-z0-9-]+)", ocr_text, re.IGNORECASE)
    date = re.search(r"\d{2}/\d{2}/\d{4}", ocr_text)
    return {
        "invoice_number": invoice_no.group(1) if invoice_no else None,
        "invoice_date": date.group(0) if date else None
    }

def build_text_rows(data, y_threshold=5):
    """Group OCR words by y-coordinate into rows."""
    rows = {}
    for i, text in enumerate(data['text']):
        if text.strip():
            y = data['top'][i]
            row_id = min(rows.keys(), key=lambda r: abs(r - y)) if rows else None
            if row_id is not None and abs(row_id - y) < y_threshold:
                rows[row_id].append((data['left'][i], text))
            else:
                rows[y] = [(data['left'][i], text)]
    return [" ".join([word for _, word in sorted(rows[y])]) for y in sorted(rows.keys())]

def get_table_text_between_markers(rows, start_kw="ITEMS", end_kw="SUMMARY"):
    """Return the concatenated text between ITEMS and SUMMARY."""
    in_table = False
    table_rows = []
    for r in rows:
        if start_kw in r:
            in_table = True
            continue
        if end_kw in r:
            break
        if in_table:
            table_rows.append(r)
    table_text = " ".join(table_rows)

    # Remove header line if present
    table_text = re.sub(
        r"No\.\s*Description\s*Qty\s*UM\s*Net price\s*Net worth\s*VAT\s*\[%\]\s*Gross\s*worth",
        " ",
        table_text,
        flags=re.IGNORECASE
    )
    return table_text.strip()

def normalize_table_text(text):
    """Fix common OCR issues to make numeric patterns match reliably."""
    t = text
    t = re.sub(r'\btks\b', ' ', t, flags=re.IGNORECASE)
    t = re.sub(r'\s+', ' ', t).strip()
    t = re.sub(r'(\d)\s+(\d{3},\d{2})', r'\1\2', t)
    t = re.sub(r'(\d+,\d{2})(?=\d)', r'\1 ', t)  
    return t

def parse_products_from_table_text(table_text):
    """
    Parse products by splitting on VAT+Gross patterns safely (no lookbehind).
    """
    t = normalize_table_text(table_text)

    # Find all product segments by manually cutting after each Gross
    matches = re.finditer(r'\d+%\s+\d{1,7},\d{2}', t)

    product_chunks = []
    start = 0
    for m in matches:
        end = m.end()
        product_chunks.append(t[start:end])
        start = end
    if start < len(t):
        product_chunks.append(t[start:])

    items = []
    for chunk in product_chunks:
        chunk = chunk.strip()
        if not chunk:
            continue

        # Extract fields
        parts = re.findall(r'\d{1,7},\d{2}', chunk)
        vat_match = re.search(r'\d+%', chunk)

        if len(parts) >= 4 and vat_match:
            qty = parts[0]
            net_price = parts[1]
            net_worth = parts[2]
            gross = parts[3]
            vat = vat_match.group(0)

            # Description = everything before Qty
            qty_index = chunk.find(qty)
            desc = chunk[:qty_index].strip()

            # Unit (like each, pcs, kg)
            unit_match = re.search(r'\b(each|pcs?|units?|set|kg|pkt)\b', chunk, re.IGNORECASE)
            unit = unit_match.group(1).lower() if unit_match else None

            # Clean description
            desc = re.sub(r'^\d+[\.:]\s*', '', desc)

            items.append({
                "Description": desc,
                "Qty": qty,
                "Unit": unit,
                "Net Price": net_price,
                "Net Worth": net_worth,
                "VAT": vat,
                "Gross": gross
            })

    return items


# ---------------- Streamlit App ----------------

st.set_page_config(page_title="Invoice Extractor (Robust Parser)", layout="wide")
st.title(" Invoice Data Extractor ")

uploaded_file = st.file_uploader("Upload an Invoice (Image or PDF)", type=["jpg", "png", "pdf"])

if uploaded_file:
    # Read image or first page of PDF
    if uploaded_file.type == "application/pdf":
        pages = convert_from_bytes(uploaded_file.read())
        img = cv2.cvtColor(np.array(pages[0]), cv2.COLOR_RGB2BGR)
    else:
        img = cv2.imdecode(np.frombuffer(uploaded_file.read(), np.uint8), cv2.IMREAD_COLOR)

    # OCR and rows
    data = extract_text_data(img)
    rows = build_text_rows(data)
    ocr_text = " ".join(data['text'])

    # Invoice fields
    fields = extract_invoice_fields(ocr_text)

    # Get table text between ITEMS and SUMMARY
    table_text = get_table_text_between_markers(rows, "ITEMS", "SUMMARY")

    # Parse products from the normalized table text
    items = parse_products_from_table_text(table_text)

    # --- UI ---
    st.write(f"**Invoice Number:** {fields['invoice_number']}")
    st.write(f"**Invoice Date:** {fields['invoice_date']}")

    st.subheader(" Extracted Line Items")
    if items:
        st.table(items)
    else:
        st.warning(" No items parsed. Click Debug below to inspect text.")

    # Download JSON
    result = {
        "invoice_number": fields['invoice_number'],
        "invoice_date": fields['invoice_date'],
        "items": items
    }
    st.download_button("⬇ Download JSON", json.dumps(result, indent=4, ensure_ascii=False),
                       file_name="invoice.json", mime="application/json")

    # Debug
    with st.expander("🔎 Debug: Table Text After Normalization"):
        st.text(normalize_table_text(table_text))
