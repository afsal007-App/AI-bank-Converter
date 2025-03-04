import streamlit as st
import pdfplumber
import pandas as pd
import re
import io

# 🔢 Convert Arabic-Indic digits to Western numerals
def convert_arabic_indic_to_western(text):
    arabic_indic_numerals = {
        '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
        '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9'
    }
    for arabic_num, western_num in arabic_indic_numerals.items():
        text = text.replace(arabic_num, western_num)
    return text

# 📝 Extract transactions and merge descriptions between dates
def extract_and_merge_transactions(pdf_bytes, opening_balance):
    transactions = []
    date_pattern = r'(\d{2}/\d{2}/\d{2})'
    amount_pattern = r'(-?\d{1,3}(?:,\d{3})*(?:\.\d{2}))'

    current_transaction = None

    with pdfplumber.open(pdf_bytes) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            lines = [convert_arabic_indic_to_western(line.strip()) for line in text.strip().split('\n') if line.strip()]

            for line in lines:
                date_match = re.search(date_pattern, line)

                if date_match:
                    if current_transaction:
                        current_transaction['Description'] = '\n'.join(current_transaction['Description']).strip()
                        transactions.append(current_transaction)

                    date = date_match.group(1)
                    line = line.replace(date, '').strip()
                    amounts = re.findall(amount_pattern, line)
                    withdrawal, balance = (amounts[:2] if len(amounts) >= 2 else (None, None))

                    if withdrawal and balance:
                        line = re.sub(amount_pattern, '', line, count=2).strip()

                    current_transaction = {
                        'Date': date,
                        'Description': [line] if line else [],
                        'Withdrawal (Dr)': withdrawal,
                        'Deposit (Cr)': None,
                        'Balance': balance,
                        'Amount': None
                    }
                else:
                    if current_transaction and line:
                        current_transaction['Description'].append(line)

    if current_transaction:
        current_transaction['Description'] = '\n'.join(current_transaction['Description']).strip()
        transactions.append(current_transaction)

    if transactions and opening_balance is not None:
        first_balance = float(transactions[0]['Balance'].replace(',', '')) if transactions[0]['Balance'] else opening_balance
        transactions.insert(0, {
            'Date': None,
            'Description': 'Opening Balance',
            'Withdrawal (Dr)': None,
            'Deposit (Cr)': None,
            'Balance': first_balance,
            'Amount': None
        })

    return pd.DataFrame(transactions)

# 📝 Process transactions: Calculate Amount and Running Balance
def process_transactions(df, opening_balance):
    df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%y', errors='coerce')
    for col in ["Withdrawal (Dr)", "Deposit (Cr)", "Balance"]:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')

    df = df[df['Balance'].notnull()].reset_index(drop=True)

    previous_balances = [opening_balance] + df['Balance'].iloc[:-1].tolist()
    df['Balance_Diff'] = df['Balance'] - pd.Series(previous_balances)

    df['Amount'] = df['Balance_Diff'].apply(lambda x: abs(x) if x > 0 else -abs(x) if x < 0 else 0)

    df['Running Balance'] = opening_balance + df['Amount'].cumsum()

    df.drop(columns=['Balance_Diff'], inplace=True)

    return df

# ✅ Streamlit Function to Process PDFs
def process(pdf_files):
    st.info("Processing Al Jazira Bank statement...")

    # Get opening balance from user input
    opening_balance = st.number_input("Enter Opening Balance:", min_value=0.0, step=0.01)

    all_transactions = []

    for pdf_file in pdf_files:
        df = extract_and_merge_transactions(pdf_file, opening_balance)

        if not df.empty:
            processed_df = process_transactions(df, opening_balance)
            all_transactions.append(processed_df)

    if all_transactions:
        final_df = pd.concat(all_transactions, ignore_index=True)
        return final_df
    else:
        st.warning("No transactions found.")
        return pd.DataFrame()
