import streamlit as st
import fitz  # PyMuPDF
import re
import pandas as pd
import io

# === Patterns ===
date_pattern = re.compile(r'^\d{2}-\d{2}-\d{4}$')

# === Extract and structure transactions ===
def extract_and_structure_transactions_from_bytes(file_bytes, filename):
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    all_lines = []

    for page in doc:
        lines = page.get_text().splitlines()
        for line in lines:
            line = line.strip()
            if line not in [
                "Transaction Date", "Value Date", "Narrative",
                "Transaction Reference", "Debit", "Credit", "Running Balance"
            ]:
                all_lines.append(line)

    transactions = []
    i = 0
    while i < len(all_lines) - 1:
        if date_pattern.match(all_lines[i]) and date_pattern.match(all_lines[i + 1]):
            txn_buffer = [all_lines[i], all_lines[i + 1]]
            i += 2
            while i < len(all_lines):
                if i + 1 < len(all_lines) and date_pattern.match(all_lines[i]) and date_pattern.match(all_lines[i + 1]):
                    break
                txn_buffer.append(all_lines[i])
                i += 1
            transactions.append(txn_buffer)
        else:
            i += 1

    structured_data = []
    for txn in transactions:
        try:
            txn_date = txn[0]
            value_date = txn[1]
            reference = txn[-4]
            debit = txn[-3]
            credit = txn[-2]
            balance = txn[-1]
            narrative = " ".join(txn[2:-4]).strip()

            structured_data.append([
                txn_date, value_date, narrative, reference, debit, credit, balance, filename
            ])
        except:
            pass

    df = pd.DataFrame(structured_data, columns=[
        "Transaction Date", "Value Date", "Narrative",
        "Transaction Reference", "Debit", "Credit", "Running Balance", "Source File"
    ])

    df = df[~df["Running Balance"].str.contains("Page", case=False, na=False)]

    for col in ["Debit", "Credit", "Running Balance"]:
        df[col] = pd.to_numeric(df[col].str.replace(",", ""), errors="coerce")

    return df

# === Streamlit Integration ===
def run():
    #st.title("Bank PDF Processor")
    st.subheader("Bank PDF Processor")

    uploaded_files = st.file_uploader("Upload ADIB Bank PDF statements", type="pdf", accept_multiple_files=True)

    if uploaded_files:
        combined_df = pd.DataFrame()

        for file in uploaded_files:
            file_bytes = file.read()
            df = extract_and_structure_transactions_from_bytes(file_bytes, file.name)
            combined_df = pd.concat([combined_df, df], ignore_index=True)

        if not combined_df.empty:
            st.dataframe(combined_df)

            # Download as CSV
            csv_data = combined_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Download CSV",
                data=csv_data,
                file_name="adib_transactions.csv",
                mime="text/csv"
            )

