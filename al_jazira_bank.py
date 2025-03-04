import streamlit as st
import pdfplumber
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

# 📝 Extract transactions from PDF
def extract_transactions(pdf_bytes):
    transactions = []
    date_pattern = r'(\d{2}/\d{2}/\d{2})'
    amount_pattern = r'(-?\d{1,3}(?:,\d{3})*(?:\.\d{2}))'

    current_transaction = None

    with pdfplumber.open(pdf_bytes) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            text = convert_arabic_indic_to_western(text)  # Convert Arabic numbers
            st.write("🔍 Extracted Text from PDF Page:\n", text[:1000])  # Debugging

            lines = [line.strip() for line in text.split('\n') if line.strip()]

            for line in lines:
                date_match = re.search(date_pattern, line)

                if date_match:
                    if current_transaction:
                        current_transaction['Description'] = '\n'.join(current_transaction['Description']).strip()
                        transactions.append(current_transaction)

                    date = date_match.group(1)
                    line = line.replace(date, '').strip()
                    amounts = re.findall(amount_pattern, line)

                    if len(amounts) >= 2:
                        withdrawal, balance = amounts[:2]
                    else:
                        withdrawal, balance = (None, None)

                    current_transaction = {
                        'Date': date,
                        'Description': [line] if line else [],
                        'Withdrawal (Dr)': withdrawal,
                        'Deposit (Cr)': None,
                        'Balance': balance
                    }
                else:
                    if current_transaction and line:
                        current_transaction['Description'].append(line)

    if current_transaction:
        current_transaction['Description'] = '\n'.join(current_transaction['Description']).strip()
        transactions.append(current_transaction)

    return pd.DataFrame(transactions)

# ✅ Streamlit Function for PDF Extraction
def process(pdf_files):
    st.info("Extracting transactions from Aljazira bank statement...")

    all_transactions = []

    for pdf_file in pdf_files:
        df = extract_transactions(pdf_file)
        if not df.empty:
            all_transactions.append(df)

    if all_transactions:
        final_df = pd.concat(all_transactions, ignore_index=True)
        return final_df
    else:
        st.warning("⚠️ No transactions found in the uploaded PDF.")
        return pd.DataFrame()
