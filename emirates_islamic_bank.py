import streamlit as st
import pdfplumber
import PyPDF2
import fitz  # PyMuPDF
import pandas as pd
import io
import re
import numpy as np

# Regular expression to match transaction entries (horizontal format)
transaction_pattern_horizontal = re.compile(
    r"(\d{2}-\d{2}-\d{4})\s+(\d{2}-\d{2}-\d{4})\s+(.+?)\s+([\d,]+\.\d{2})?\s+([\d,]+\.\d{2})?\s+([\d,]+\.\d{2})?"
)

# Function to extract text using PyPDF2
def extract_text_pypdf2(pdf_bytes):
    text = ""
    pdf_bytes.seek(0)
    reader = PyPDF2.PdfReader(pdf_bytes)
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

# Function to extract text using PyMuPDF (fitz)
def extract_text_pymupdf(pdf_bytes):
    text = ""
    pdf_bytes.seek(0)
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    for page in doc:
        text += page.get_text("text") + "\n"
    return text

# Function to extract text using pdfplumber
def extract_text_pdfplumber(pdf_bytes):
    text = ""
    pdf_bytes.seek(0)
    with pdfplumber.open(pdf_bytes) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

# Function to extract transactions from text (horizontal format)
def extract_transactions_horizontal(text):
    transactions = []
    lines = text.split("\n")
    for line in lines:
        match = transaction_pattern_horizontal.match(line)
        if match:
            transaction_date = match.group(1).strip()
            value_date = match.group(2).strip()
            narration = match.group(3).strip()
            debit_amount = match.group(4) or "0.00"
            credit_amount = match.group(5) or "0.00"
            running_balance = match.group(6) or "0.00"
            transactions.append([transaction_date, value_date, narration, debit_amount, credit_amount, running_balance])
    return transactions

# Function to extract transactions using a vertical method (table-based)
def extract_transactions_vertical(pdf_bytes):
    transactions = []
    pdf_bytes.seek(0)
    with pdfplumber.open(pdf_bytes) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                for row in table:
                    if len(row) >= 6:
                        transactions.append(row)
    return transactions

# Function to process multiple PDFs
def process(pdf_files):
    st.info("Processing Emirates Islamic Bank statement...")

    all_transactions = []
    for pdf_file in pdf_files:
        text_pypdf2 = extract_text_pypdf2(pdf_file)
        text_pymupdf = extract_text_pymupdf(pdf_file)
        text_pdfplumber = extract_text_pdfplumber(pdf_file)

        text = max([text_pypdf2, text_pymupdf, text_pdfplumber], key=len)

        transactions_horizontal = extract_transactions_horizontal(text)
        transactions_vertical = extract_transactions_vertical(pdf_file)

        all_transactions.extend(transactions_horizontal)
        all_transactions.extend(transactions_vertical)

    # Create DataFrame
    columns = ["Transaction Date", "Value Date", "Narration", "Debit Amount", "Credit Amount", "Running Balance"]
    df = pd.DataFrame(all_transactions, columns=columns)

    # Debugging: Show transaction count before filtering
    st.write("\ud83d\udcca Transactions Before Cleaning:", df.shape)

    # ✅ 1. Standardize all values to string & strip whitespace
    df = df.astype(str).apply(lambda x: x.str.strip())

    # ✅ 2. Convert "nan" and "None" values to real NaN
    df.replace(["nan", "None", "N/A", ""], np.nan, inplace=True)

    # ✅ 3. Remove invalid "Value Date" headers appearing as rows
    df = df[~df["Transaction Date"].str.contains("Value Date", na=False, case=False)]
    df = df[~df["Narration"].str.contains("Narration", na=False, case=False)]

    # ✅ 4. Remove rows where "Transaction Date" is blank or NaN
    df = df.dropna(subset=["Transaction Date"])

    # ✅ 5. Convert Transaction Date to datetime
    df["Transaction Date"] = pd.to_datetime(df["Transaction Date"], format="%d-%m-%Y", errors="coerce")

    # ✅ 6. Remove rows where "Transaction Date" is still NaN (invalid dates)
    df = df.dropna(subset=["Transaction Date"])

    # ✅ 7. Sort transactions
    df = df.sort_values(by="Transaction Date", ascending=True)

    # ✅ 8. Normalize text columns to prevent minor variations causing duplicates
    df["Narration"] = df["Narration"].str.lower().str.strip()

    # ✅ 9. Convert amount fields to numeric (removing commas)
    df["Debit Amount"] = df["Debit Amount"].str.replace(",", "").astype(float)
    df["Credit Amount"] = df["Credit Amount"].str.replace(",", "").astype(float)
    df["Running Balance"] = df["Running Balance"].str.replace(",", "").astype(float)

    # ✅ 10. Remove duplicate transactions based on relevant columns
    df = df.drop_duplicates(subset=["Transaction Date", "Value Date", "Narration", "Debit Amount", "Credit Amount"])

    # Debugging: Show transaction count after removing duplicates
    st.write("\ud83d\udcca Transactions After Removing Duplicates:", df.shape)

    if df.empty:
        st.warning("⚠️ No valid transactions found after filtering. Please check if the correct PDF is uploaded.")
    
    return df
