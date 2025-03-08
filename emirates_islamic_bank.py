import pdfplumber
import fitz  # PyMuPDF
import pytesseract
import re
import pandas as pd
import io

def extract_text_from_pdf(pdf_file):
    """Extract text from a PDF, trying searchable first then OCR if needed."""
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        # If text is too short, assume it's scanned and use OCR
        if len(text.strip()) < 100:
            text = extract_text_from_scanned_pdf(pdf_file)
    except Exception:
        text = extract_text_from_scanned_pdf(pdf_file)
    return text

def extract_text_from_scanned_pdf(pdf_file):
    """Extract text from scanned PDFs using OCR."""
    text = ""
    pdf_document = fitz.open(stream=pdf_file.getvalue(), filetype="pdf")
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        pix = page.get_pixmap()
        img_bytes = pix.tobytes("png")
        text += pytesseract.image_to_string(img_bytes) + "\n"
    pdf_document.close()
    return text

def parse_transactions(text):
    """Parse transaction data from extracted text."""
    lines = text.splitlines()
    # Define the header to locate the transaction table
    header_line = "Transaction Date Value Date Narration Debit Credit Running Balance"
    try:
        header_index = next(i for i, line in enumerate(lines) if header_line.lower() in line.lower())
    except StopIteration:
        return []
    
    transaction_lines = lines[header_index + 1:]
    # Pattern to detect the start of a transaction (two dates)
    start_pattern = r'^\d{2}-\d{2}-\d{4}\s+\d{2}-\d{2}-\d{4}'
    # Pattern to extract transaction fields
    extract_pattern = r'^(\d{2}-\d{2}-\d{4})\s+(\d{2}-\d{2}-\d{4})\s+(.*?)\s+(\d{1,3}(,\d{3})*\.\d{2}|\d+\.\d{2})\s+(\d{1,3}(,\d{3})*\.\d{2}|\d+\.\d{2})\s+(\d{1,3}(,\d{3})*\.\d{2}|\d+\.\d{2})$'
    
    transactions = []
    current_transaction = []
    
    for line in transaction_lines:
        line = line.strip()
        if not line:
            continue
        if re.match(start_pattern, line):
            if current_transaction:
                # Process the previous transaction
                transaction_str = ' '.join(current_transaction).strip()
                transaction_str = re.sub(r'\s+', ' ', transaction_str)
                match = re.match(extract_pattern, transaction_str)
                if match:
                    trans_date, value_date, narration, debit, credit, balance = match.groups()
                    transactions.append({
                        'Transaction Date': trans_date,
                        'Value Date': value_date,
                        'Narration': narration,
                        'Debit': debit,
                        'Credit': credit,
                        'Running Balance': balance
                    })
                current_transaction = []
            current_transaction.append(line)
        else:
            if current_transaction:
                current_transaction.append(line)
    
    # Process the last transaction
    if current_transaction:
        transaction_str = ' '.join(current_transaction).strip()
        transaction_str = re.sub(r'\s+', ' ', transaction_str)
        match = re.match(extract_pattern, transaction_str)
        if match:
            trans_date, value_date, narration, debit, credit, balance = match.groups()
            transactions.append({
                'Transaction Date': trans_date,
                'Value Date': value_date,
                'Narration': narration,
                'Debit': debit,
                'Credit': credit,
                'Running Balance': balance
            })
    
    return transactions

def process(pdf_files):
    """Process a list of PDF files and return a combined DataFrame."""
    all_transactions = []
    for pdf_file in pdf_files:
        text = extract_text_from_pdf(pdf_file)
        transactions = parse_transactions(text)
        all_transactions.extend(transactions)
    
    df = pd.DataFrame(all_transactions)
    return df
