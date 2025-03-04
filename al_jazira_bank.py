import streamlit as st
import pdfplumber
import PyPDF2
import fitz  # PyMuPDF
import pandas as pd
import re
from io import BytesIO

# 🔢 Convert Arabic-Indic digits to Western numerals
def convert_arabic_indic_to_western(text):
    arabic_indic_numerals = {
        '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
        '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9'
    }
    for arabic_num, western_num in arabic_indic_numerals.items():
        text = text.replace(arabic_num, western_num)
    return text

# 📝 Extract text using PyPDF2
def extract_text_pypdf2(pdf_bytes):
    text = ""
    pdf_bytes.seek(0)
    reader = PyPDF2.PdfReader(pdf_bytes)
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

# 📝 Extract text using PyMuPDF (fitz)
def extract_text_pymupdf(pdf_bytes):
    text = ""
    pdf_bytes.seek(0)
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    for page in doc:
        text += page.get_text("text") + "\n"
    return text

# 📝 Extract transactions using pdfplumber (Table Extraction)
def extract_transactions_pdfplumber(pdf_bytes):
    transactions = []
    
    with pdfplumber.open(pdf_bytes) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table:
                continue  # Skip if no table is found

            df = pd.DataFrame(table)

            # Debugging: Show extracted table
            st.write("📊 Extracted Table Data (PDFPlumber):", df.head())

            # Define column names (Adjust based on actual PDF structure)
            df.columns = ["Transaction Date", "Value Date", "Description", "Withdrawal (Dr)", "Deposit (Cr)", "Running Balance"]

            # Drop empty or invalid rows
            df = df.dropna(subset=["Transaction Date", "Description"]).reset_index(drop=True)

            # Apply Arabic-Indic conversion
            df = df.applymap(lambda x: convert_arabic_indic_to_western(str(x)) if pd.notnull(x) else x)

            # Append to transactions list
            transactions.append(df)

    if transactions:
        return pd.concat(transactions, ignore_index=True)
    else:
        return pd.DataFrame(columns=["Transaction Date", "Value Date", "Description", "Withdrawal (Dr)", "Deposit (Cr)", "Running Balance"])

# ✅ Streamlit Function for PDF Extraction Using Multiple Methods
def process(pdf_files):
    st.info("Extracting transactions from Aljazira bank statement using multiple methods...")

    all_transactions = []

    for pdf_file in pdf_files:
        # Extract using PyPDF2
        text_pypdf2 = extract_text_pypdf2(pdf_file)

        # Extract using PyMuPDF (fitz)
        text_pymupdf = extract_text_pymupdf(pdf_file)

        # Extract table-based structured data using pdfplumber
        df_pdfplumber = extract_transactions_pdfplumber(pdf_file)

        # Debugging: Show extracted raw text
        st.write("📜 Extracted Text (PyPDF2):", text_pypdf2[:1000])  # Show first 1000 chars
        st.write("📜 Extracted Text (PyMuPDF):", text_pymupdf[:1000])

        # If table-based extraction works, prioritize it
        if not df_pdfplumber.empty:
            all_transactions.append(df_pdfplumber)

    if all_transactions:
        final_df = pd.concat(all_transactions, ignore_index=True)
        return final_df
    else:
        st.warning("⚠️ No structured transactions found in the uploaded PDF.")
        return pd.DataFrame()
