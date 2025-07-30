# Invoice Data Extractor using OCR 

This project is a full-stack **OCR-based Invoice Data Extraction tool** built with **Python** and **Streamlit**. It allows you to upload invoice images or PDFs and automatically extract:  

- Invoice Number & Date  
- All line items (Description, Quantity, Unit, Net Price, Net Worth, VAT %, Gross Total)  

It works robustly even when invoices have irregular layouts or merged lines, thanks to custom text normalization and a **pattern-based parser**.  

---

## Demo
👉 Upload any invoice image (JPG/PNG) or PDF in the app UI.  
The extracted data will be displayed in a table and can be downloaded as a JSON file.  

---

## Dataset

The invoice images used for testing and model evaluation are taken from the **High-Quality Invoice Images for OCR** dataset:  
🔗 [https://www.kaggle.com/datasets/osamahosamabdellatif/high-quality-invoice-images-for-ocr](https://www.kaggle.com/datasets/osamahosamabdellatif/high-quality-invoice-images-for-ocr)

---

## Features

- **OCR using Tesseract**: Automatically reads invoice text with `pytesseract`.
- **Custom text grouping**: Groups text into rows based on y-coordinates.
- **Robust parser**: Extracts products by numeric signatures (Qty, Price, VAT, etc.) even with merged lines.
- **Streamlit UI**:  
  - Upload image or PDF invoices  
  - Visual display of extracted data  
  - Download JSON file  
- **Supports multi-line descriptions** and irregular table structures.

---

## Output
- Extracted invoice metadata: Invoice number, date

- Line item table:

    - Description

    - Quantity

    - Unit (each, pcs, etc.)

    - Net Price, Net Worth

    - VAT (%)

    - Gross Total

- Download extracted data as JSON.

