import streamlit as st
import pdfplumber
import re
import pandas as pd

# ---------------------- PDF Parsing Logic ----------------------

account_start_marker = "ACCOUNT STATEMENT ACCOUNT HOLDER NAME ACCOUNT TYPE CURRENCY"
txn_pattern = re.compile(
    r"(\d{2}/\d{2}/\d{4})\s+(\w+)\s+(.+?)\s+(-?\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s+(-?\d{1,3}(?:,\d{3})*(?:\.\d+)?)"
)

def process_wio_pdfs(pdf_files):
    all_transactions = []

    for pdf_file in pdf_files:
        all_lines = []

        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    all_lines.extend(text.splitlines())

        # Identify blocks
        blocks = []
        current_block = []

        for line in all_lines:
            if account_start_marker in line:
                if current_block:
                    blocks.append(current_block)
                    current_block = []
            current_block.append(line)
        if current_block:
            blocks.append(current_block)

        # Process blocks
        for block in blocks:
            block_text = "\n".join(block)

            # Account Number
            acct_match = re.search(r"\b(\d{10})\b", block_text)
            account_number = acct_match.group(1) if acct_match else "Unknown"

            # Currency
            currency_match = re.search(r"(Current|Savings)\s+([A-Z]{3})", block_text)
            currency = currency_match.group(2) if currency_match else "Unknown"

            # Transaction lines
            for i, line in enumerate(block):
                if "Date Ref. Number" in line or (line.startswith("Date") and "Description" in line):
                    txn_start = i + 1
                    break
            else:
                txn_start = 0

            for line in block[txn_start:]:
                line = line.strip()
                match = txn_pattern.match(line)
                if match:
                    date = match.group(1)
                    ref = match.group(2)
                    desc = match.group(3).strip()
                    amount = float(match.group(4).replace(",", ""))
                    balance = float(match.group(5).replace(",", ""))
                    all_transactions.append({
                        "Date": date,
                        "Ref. Number": ref,
                        "Description": desc,
                        "Amount (Incl. VAT)": amount,
                        "Balance": balance,
                        "Currency": currency,
                        "Account Number": account_number,
                        "Source File": pdf_file.name
                    })

    return pd.DataFrame(all_transactions)

# ---------------------- Streamlit UI ----------------------

def run():
    st.header("Bank PDF Processor")

    uploaded_files = st.file_uploader("Upload one or more Wio Bank PDF statements", type="pdf", accept_multiple_files=True)

    if uploaded_files:
        st.info("Processing uploaded file(s)...")
        df = process_wio_pdfs(uploaded_files)

        if df.empty:
            st.warning("⚠️ No transactions found in any uploaded files.")
        else:
            st.success(f"✅ Extracted {len(df)} transactions from {len(uploaded_files)} PDF(s)")
            st.dataframe(df)

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv, "wio_bank_transactions.csv", "text/csv")
