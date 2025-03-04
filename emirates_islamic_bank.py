import streamlit as st
import pdfplumber
import PyPDF2
import fitz  # PyMuPDF
import pandas as pd
import io
import re

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

# Function to extract transactions from text
def extract_transactions_horizontal(text):
    transactions = []
    lines = text.split("\n")

    for i in range(len(lines)):
        match = transaction_pattern_horizontal.match(lines[i])
        if match:
            transaction_date = match.group(1).strip()
            value_date = match.group(2).strip()
            narration = match.group(3).strip()
            debit_amount = match.group(4) or "0.00"
            credit_amount = match.group(5) or "0.00"
            running_balance = match.group(6) or "0.00"
            transactions.append([transaction_date, value_date, narration, debit_amount, credit_amount, running_balance])

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

        all_transactions.extend(transactions_horizontal)

    # Create DataFrame
    columns = ["Transaction Date", "Value Date", "Narration", "Debit Amount", "Credit Amount", "Running Balance"]
    df = pd.DataFrame(all_transactions, columns=columns)

    # Convert Transaction Date to datetime
    df["Transaction Date"] = pd.to_datetime(df["Transaction Date"], format="%d-%m-%Y", errors="coerce")
    df = df.sort_values(by="Transaction Date", ascending=True)

    return df
