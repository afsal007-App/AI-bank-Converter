import streamlit as st
import pdf2image
import pytesseract
import re
import pandas as pd
from io import BytesIO

# Function to extract text from a PDF page image using OCR
def extract_text_from_image(image):
    """Extract text from an image using Tesseract OCR."""
    return pytesseract.image_to_string(image)

# Function to parse transactions from extracted text
def parse_transactions(text):
    """Parse transaction data from text based on a specific format."""
    # Split text into lines
    lines = text.splitlines()
    # Define the header to identify the start of transactions
    header_line = "Transaction Date Value Date Narration Debit Credit Running Balance"
    try:
        # Find the index of the header line
        header_index = next(i for i, line in enumerate(lines) if header_line in line)
    except StopIteration:
        return []  # No header found, likely no transactions
    
    # Get lines after the header
    transaction_lines = lines[header_index + 1:]
    
    # Regular expressions to identify and extract transactions
    start_pattern = r'^\d{2}-\d{2}-\d{4}\s+\d{2}-\d{2}-\d{4}'  # Matches two dates at the start
    extract_pattern = r'^(\d{2}-\d{2}-\d{4})\s+(\d{2}-\d{2}-\d{4})\s+(.*?)\s+(\d{1,3}(,\d{3})*\.\d{2})\s+(\d{1,3}(,\d{3})*\.\d{2})\s+(\d{1,3}(,\d{3})*\.\d{2})$'
    
    transactions = []
    current_transaction = []
    
    for line in transaction_lines:
        line = line.strip()
        if not line:
            continue
        # If line starts with two dates, it’s a new transaction
        if re.match(start_pattern, line):
            if current_transaction:
                # Process the previous transaction
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
    
    # Process the last transaction, if any
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

# Main Streamlit application
def main():
    """Run the Streamlit app to process PDFs and generate a sorted Excel file."""
    st.title("PDF Transaction Extractor")
    
    # File uploader for multiple PDFs
    uploaded_files = st.file_uploader(
        "Upload PDF files",
        type="pdf",
        accept_multiple_files=True
    )
    
    if uploaded_files:
        all_transactions = []
        
        # Show a spinner while processing
        with st.spinner("Processing PDFs..."):
            for uploaded_file in uploaded_files:
                # Convert PDF to images (one per page)
                images = pdf2image.convert_from_bytes(uploaded_file.read())
                for image in images:
                    # Extract text from each page
                    text = extract_text_from_image(image)
                    # Parse transactions from the text
                    transactions = parse_transactions(text)
                    all_transactions.extend(transactions)
        
        if all_transactions:
            # Create a DataFrame from all transactions
            df = pd.DataFrame(all_transactions)
            
            # Convert 'Transaction Date' to datetime for sorting
            df['Transaction Date'] = pd.to_datetime(df['Transaction Date'], format='%d-%m-%Y')
            
            # Sort by 'Transaction Date'
            df = df.sort_values('Transaction Date')
            
            # Convert back to string format for Excel
            df['Transaction Date'] = df['Transaction Date'].dt.strftime('%d-%m-%Y')
            
            # Generate Excel file in memory
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
            output.seek(0)
            
            # Provide a download button for the Excel file
            st.download_button(
                label="Download Excel file",
                data=output,
                file_name="transactions.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.write("No transactions found in the uploaded PDFs.")

if __name__ == "__main__":
    main()
