import streamlit as st
import pdfplumber
import PyPDF2
import fitz  # PyMuPDF
import pandas as pd
import io
import re
import numpy as np
from pdf2image import convert_from_bytes
import pytesseract

# Function to extract text from a PDF
def extract_text_from_pdf(pdf_file):
    """Extract text from a PDF using pdfplumber for searchable PDFs or OCR for scanned PDFs."""
    text = ""
    # Convert UploadedFile to BytesIO if necessary
    if hasattr(pdf_file, 'read'):
        pdf_file = io.BytesIO(pdf_file.read())
    
    # Try extracting text with pdfplumber (for searchable PDFs)
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        # If text is too short, assume it's a scanned PDF and use OCR
        if len(text.strip()) < 100:
            text = extract_text_from_scanned_pdf(pdf_file)
    except Exception as e:
        st.error(f"Error extracting text with pdfplumber: {e}")
        text = extract_text_from_scanned_pdf(pdf_file)
    
    return text

# Function to extract text from scanned PDFs using OCR
def extract_text_from_scanned_pdf(pdf_file):
    """Extract text from a scanned PDF using OCR."""
    text = ""
    try:
        # Convert PDF to images using fitz
        pdf_document = fitz.open(stream=pdf_file.getvalue(), filetype="pdf")
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            pix = page.get_pixmap()
            img = pix.tobytes("png")
            text += pytesseract.image_to_string(img) + "\n"
    except Exception as e:
        st.error(f"Error extracting text from scanned PDF: {e}")
    return text

# Function to parse transactions from extracted text
def parse_transactions(text):
    """Parse transaction data from extracted text."""
    lines = text.splitlines()
    header_line = "Transaction Date Value Date Narration Debit Credit Running Balance"
    try:
        header_index = next(i for i, line in enumerate(lines) if header_line in line)
    except StopIteration:
        st.warning("No transaction table found in the PDF.")
        return []
    
    transaction_lines = lines[header_index + 1:]
    start_pattern = r'^\d{2}-\d{2}-\d{4}\s+\d{2}-\d{2}-\d{4}'  # Matches two dates at the start
    extract_pattern = r'^(\d{2}-\d{2}-\d{4})\s+(\d{2}-\d{2}-\d{4})\s+(.*?)\s+(\d{1,3}(,\d{3})*\.\d{2})\s+(\d{1,3}(,\d{3})*\.\d{2})\s+(\d{1,3}(,\d{3})*\.\d{2})$'
    
    transactions = []
    current_transaction = []
    
    for line in transaction_lines:
        line = line.strip()
        if not line:
            continue
        if re.match(start_pattern, line):
            if current_transaction:
                transaction_str = ' '.join(current_transaction)
                transaction_str = re.sub(r'\s+', ' ', transaction_str).strip()
                match = re.match(extract_pattern, transaction_str)
                if match:
                    trans_date, value_date, narration, debit, credit, running_balance = match.groups()
                    transactions.append({
                        'Transaction Date': trans_date,
                        'Value Date': value_date,
                        'Narration': narration,
                        'Debit': debit,
                        'Credit': credit,
                        'Running Balance': running_balance
                    })
                current_transaction = []
            current_transaction.append(line)
        else:
            if current_transaction:
                current_transaction.append(line)
    
    # Process the last transaction
    if current_transaction:
        transaction_str = ' '.join(current_transaction)
        transaction_str = re.sub(r'\s+', ' ', transaction_str).strip()
        match = re.match(extract_pattern, transaction_str)
        if match:
            trans_date, value_date, narration, debit, credit, running_balance = match.groups()
            transactions.append({
                'Transaction Date': trans_date,
                'Value Date': value_date,
                'Narration': narration,
                'Debit': debit,
                'Credit': credit,
                'Running Balance': running_balance
            })
    
    return transactions

# Function to process uploaded PDFs
def process(pdf_files):
    """Process a list of PDF files and return a DataFrame of transactions."""
    all_transactions = []
    for pdf_file in pdf_files:
        text = extract_text_from_pdf(pdf_file)
        transactions = parse_transactions(text)
        all_transactions.extend(transactions)
    
    df = pd.DataFrame(all_transactions)
    return df

# Streamlit app
def main():
    st.title("PDF Transaction Extractor")
    st.write("Upload one or more PDF bank statements to extract transaction data.")

    # File uploader
    uploaded_files = st.file_uploader("Choose PDF files", type="pdf", accept_multiple_files=True)
    
    if uploaded_files:
        # Process the uploaded PDFs
        with st.spinner("Processing PDFs..."):
            df = process(uploaded_files)
        
        if not df.empty:
            # Sort by Transaction Date
            df['Transaction Date'] = pd.to_datetime(df['Transaction Date'], format='%d-%m-%Y')
            df = df.sort_values('Transaction Date')
            df['Transaction Date'] = df['Transaction Date'].dt.strftime('%d-%m-%Y')
            
            # Display the DataFrame
            st.subheader("Extracted Transactions")
            st.dataframe(df)
            
            # Option to download the data as CSV
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download as CSV",
                data=csv,
                file_name="transactions.csv",
                mime="text/csv"
            )
        else:
            st.error("No transactions could be extracted from the uploaded PDFs.")

if __name__ == "__main__":
    main()
