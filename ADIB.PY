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
    st.header("ADIB Bank PDF Processor")

    uploaded_files = st.file_uploader("Upload ADIB Bank PDF statements", type="pdf", accept_multiple_files=True)

    if uploaded_files:
        combined_df = pd.DataFrame()

        for uploaded_file in uploaded_files:
            file_bytes = uploaded_file.read()
            df = extract_and_structure_transactions_from_bytes(file_bytes, uploaded_file.name)
            st.markdown(f"✅ **{uploaded_file.name}** → {len(df)} transactions")
            combined_df = pd.concat([combined_df, df], ignore_index=True)

        if not combined_df.empty:
            st.success(f"🎉 Total transactions extracted: **{len(combined_df)}**")
            st.dataframe(combined_df)

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                combined_df.to_excel(writer, index=False, sheet_name='Transactions')
                worksheet = writer.sheets['Transactions']
                for i, col in enumerate(combined_df.columns):
                    max_len = combined_df[col].astype(str).map(len).max()
                    worksheet.set_column(i, i, max_len + 2)

            st.download_button(
                label="📥 Download Excel File",
                data=output.getvalue(),
                file_name="adib_transactions.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
