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

# 📝 Extract transactions using structural table extraction (column-wise)
def extract_transactions_structural(pdf_bytes):
    transactions = []
    with pdfplumber.open(pdf_bytes) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table:
                continue

            df = pd.DataFrame(table)

            # Set expected column names (adjust if needed)
            df.columns = ["Transaction Date", "Value Date", "Description", "Withdrawal (Dr)", "Deposit (Cr)", "Running Balance"]
            df = df.dropna(subset=["Transaction Date", "Description"]).reset_index(drop=True)

            # Convert Arabic-Indic numerals to Western
            df = df.applymap(lambda x: convert_arabic_indic_to_western(str(x)) if pd.notnull(x) else x)

            for _, row in df.iterrows():
                transaction = {
                    "Transaction Date": row["Transaction Date"],
                    "Value Date": row["Value Date"],
                    "Description": row["Description"],
                    "Withdrawal (Dr)": row["Withdrawal (Dr)"],
                    "Deposit (Cr)": row["Deposit (Cr)"],
                    "Running Balance": row["Running Balance"]
                }
                transactions.append(transaction)

    return pd.DataFrame(transactions)

# ✅ Processing multiple PDFs
def process(pdf_files):
    st.info("Extracting transactions from Aljazira Bank statements...")

    all_transactions = []

    for pdf_file in pdf_files:
        df = extract_transactions_structural(pdf_file)
        if not df.empty:
            all_transactions.append(df)

    if all_transactions:
        final_df = pd.concat(all_transactions, ignore_index=True)
        return final_df
    else:
        return pd.DataFrame()

# ✅ Required run() function for Streamlit
def run():
    #st.header("Bank PDF Processor")
    st.subheader("Bank PDF Processor")

    uploaded_files = st.file_uploader(
        "Upload Al Jazira Bank PDF statements",
        type="pdf",
        accept_multiple_files=True
    )

    if uploaded_files:
        df = process(uploaded_files)

        if df.empty:
            st.warning("⚠️ No structured transactions found in the uploaded PDFs.")
        else:
            st.success("✅ Transactions extracted successfully!")
            st.dataframe(df)

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv, "al_jazira_transactions.csv", "text/csv")
