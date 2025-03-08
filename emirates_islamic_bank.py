import pdfplumber
import re
import pandas as pd
from pdf2image import convert_from_bytes
import pytesseract

def parse_transactions(text):
    """Parse transaction data from text based on a specific format."""
    lines = text.splitlines()
    header_line = "Transaction Date Value Date Narration Debit Credit Running Balance"
    try:
        header_index = next(i for i, line in enumerate(lines) if header_line in line)
    except StopIteration:
        return []
    
    transaction_lines = lines[header_index + 1:]
    start_pattern = r'^\d{2}-\d{2}-\d{4}\s+\d{2}-\d{2}-\d{4}'
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

def process(pdf_files):
    """Process a list of PDF files and extract transactions."""
    all_transactions = []
    for pdf_file in pdf_files:
        # Try extracting text with pdfplumber (for searchable PDFs)
        with pdfplumber.open(pdf_file) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        # If little text is extracted, assume scanned PDF and use OCR
        if len(text.strip()) < 100:
            images = convert_from_bytes(pdf_file.getvalue())
            text = ""
            for image in images:
                text += pytesseract.image_to_string(image) + "\n"
        
        # Parse transactions
        transactions = parse_transactions(text)
        all_transactions.extend(transactions)
    
    df = pd.DataFrame(all_transactions)
    return df
