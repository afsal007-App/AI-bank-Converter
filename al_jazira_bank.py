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

# 📝 Extract text using pdfplumber
def extract_text_pdfplumber(pdf_bytes):
    text = ""
    pdf_bytes.seek(0)
    with pdfplumber.open(pdf_bytes) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

# ✅ Streamlit Function to Extract Raw Data
def process(pdf_files):
    st.info("Extracting text from Aljazira bank statement...")

    all_texts = []

    for pdf_file in pdf_files:
        text_pypdf2 = extract_text_pypdf2(pdf_file)
        text_pymupdf = extract_text_pymupdf(pdf_file)
        text_pdfplumber = extract_text_pdfplumber(pdf_file)

        # Convert Arabic-Indic numbers
        text_pypdf2 = convert_arabic_indic_to_western(text_pypdf2)
        text_pymupdf = convert_arabic_indic_to_western(text_pymupdf)
        text_pdfplumber = convert_arabic_indic_to_western(text_pdfplumber)

        # Debugging: Show Extracted Text
        st.write("📜 Extracted Text (PyPDF2):", text_pypdf2[:1000])  # First 1000 chars
        st.write("📜 Extracted Text (PyMuPDF):", text_pymupdf[:1000])
        st.write("📜 Extracted Text (pdfplumber):", text_pdfplumber[:1000])

        # Store all extracted text for analysis
        all_texts.append(text_pypdf2)
        all_texts.append(text_pymupdf)
        all_texts.append(text_pdfplumber)

    if not any(all_texts):
        st.warning("⚠️ No text was extracted. The PDF may be scanned.")
    return all_texts
