# Rak_Bank.py – Example Streamlit-compatible Bank Parser Module

import fitz  # PyMuPDF
import re
import pandas as pd
import os
import streamlit as st
from io import BytesIO

# Regular expression to identify date format
date_pattern = re.compile(r'^\d{2}-[A-Za-z]{3}-\d{4}')

def process_pdf(pdf_file, filename="uploaded_file.pdf"):
    transactions = []
    current_trans = None

    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")

    for page in doc:
        lines = page.get_text("text").splitlines()

        # Identify start of transaction lines
        start_idx = 0
        for i, line in enumerate(lines):
            if line.strip().startswith("Date") and "Balance" in line:
                start_idx = i + 1
                break

        for line in lines[start_idx:]:
            clean_line = line.strip()
            clean_line_lower = clean_line.lower()

            if not clean_line or any(keyword in clean_line_lower for keyword in [
                "page", "date issued", "your current account transactions",
                "account type: current account", "الإصدار", "مدة الكشف"
            ]):
                continue

            if date_pattern.match(clean_line):
                if current_trans:
                    transactions.append(current_trans)

                parts = clean_line.split(maxsplit=1)
                date = parts[0]
                description = parts[1] if len(parts) > 1 else ""

                current_trans = {
                    "PDF_File": filename,
                    "Date": date,
                    "Description": description,
                    "Cheque": None,
                    "Withdrawal": None,
                    "Deposit": None,
                    "Balance": None
                }
            else:
                if current_trans:
                    current_trans["Description"] += " " + clean_line

    if current_trans:
        transactions.append(current_trans)

    for trans in transactions:
        desc = trans["Description"]
        desc = desc.replace(" Cr.", "").replace(" Dr.", "")
        amounts = re.findall(r'\d[\d,]*\.\d{2}', desc)

        if len(amounts) >= 2:
            amount_str = amounts[-2]
            balance_str = amounts[-1]

            trans["Balance"] = float(balance_str.replace(",", ""))
            amount_value = float(amount_str.replace(",", ""))

            desc_lower = desc.lower()
            if any(word in desc_lower for word in ["transfer from", "deposit", "credit", "funds transfer"]):
                trans["Deposit"] = amount_value
                trans["Withdrawal"] = None
            else:
                trans["Withdrawal"] = amount_value
                trans["Deposit"] = None

            trans["Description"] = desc[:desc.rfind(amount_str)].strip()
        else:
            trans["Balance"] = None

    return transactions

def run():
    st.subheader("Bank PDF Processor")
    uploaded_files = st.file_uploader("Upload one or more PDF files", type="pdf", accept_multiple_files=True)

    if uploaded_files:
        all_transactions = []
        for uploaded_file in uploaded_files:
            st.info(f"Processing: {uploaded_file.name}")
            transactions = process_pdf(uploaded_file, uploaded_file.name)
            all_transactions.extend(transactions)

        if all_transactions:
            df = pd.DataFrame(all_transactions)

            # Drop unwanted description lines
            df = df[~df["Description"].str.contains(
                "account type: current account|الإصدار|مدة الكشف",
                case=False, na=False
            )]

            st.success("Transactions Extracted:")
            st.dataframe(df)

            # CSV download
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download CSV", csv, "transactions.csv", "text/csv")
