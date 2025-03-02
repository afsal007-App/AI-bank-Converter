# -*- coding: utf-8 -*-

import streamlit as st
import pdfplumber
import pytesseract
from pdf2image import convert_from_path
import pandas as pd
import re
import spacy
import io
import os

# Ensure spaCy model is installed before loading
MODEL_NAME = "en_core_web_sm"
try:
    nlp = spacy.load(MODEL_NAME)
except OSError:
    os.system(f"python -m spacy download {MODEL_NAME}")
    nlp = spacy.load(MODEL_NAME)

# Extract text from PDFs
def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

# OCR-based extraction
def extract_text_with_ocr(pdf_path):
    images = convert_from_path(pdf_path)
    text = "\n".join([pytesseract.image_to_string(img) for img in images])
    return text

# Extract transactions using regex
def extract_transactions(text):
    transactions = []
    pattern = re.compile(r"(\d{2}/\d{2}/\d{4})\s+(.+?)\s+(-?\d{1,3}(?:,\d{3})*\.\d{2})?\s+(-?\d{1,3}(?:,\d{3})*\.\d{2})?")
    
    matches = pattern.findall(text)
    for match in matches:
        date, description, debit, credit = match
        transactions.append({
            "Date": date,
            "Description": description.strip(),
            "Debit": float(debit.replace(',', '')) if debit else 0.00,
            "Credit": float(credit.replace(',', '')) if credit else 0.00
        })
    return transactions

# Convert transactions to Excel
def save_to_excel(transactions):
    output = io.BytesIO()
    df = pd.DataFrame(transactions)
    df.to_excel(output, index=False)
    output.seek(0)
    return output

# Streamlit Web App UI
st.title("🏦 AI Bank Statement Converter")
st.write("Upload a bank statement in PDF format, and the app will extract transactions automatically.")

uploaded_file = st.file_uploader("Upload a Bank Statement PDF", type=["pdf"])

if uploaded_file:
    st.success("✅ PDF uploaded successfully! Extracting transactions...")

    # Extract text from PDF
    text = extract_text_from_pdf(uploaded_file)
    if not text.strip():
        st.warning("⚠️ No selectable text found, using OCR instead...")
        text = extract_text_with_ocr(uploaded_file)

    # Extract transactions
    transactions = extract_transactions(text)
    
    if transactions:
        st.subheader("📜 Extracted Transactions")
        df_transactions = pd.DataFrame(transactions)
        st.dataframe(df_transactions)

        # Provide download option
        excel_output = save_to_excel(transactions)
        st.download_button(
            label="⬇️ Download Extracted Transactions as Excel",
            data=excel_output,
            file_name="bank_statement.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("⚠️ No transactions were detected in the uploaded PDF.")
