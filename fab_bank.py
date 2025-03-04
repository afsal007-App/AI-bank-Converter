import streamlit as st
import pdfplumber
import pandas as pd
import re
import io

# ---------------------------
# FAB Extraction Function
# ---------------------------
def extract_fab_transactions(pdf_file):
    transactions = []
    combined_text = ""

    pdf_file.seek(0)
    with pdfplumber.open(io.BytesIO(pdf_file.read())) as pdf:
        combined_text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

    # Debugging: Show raw extracted text
    st.write("📜 Extracted Text (FAB):", combined_text[:1000])  # Show first 1000 characters

    # FAB transaction regex pattern
    full_desc_pattern = re.compile(
        r"(\d{2} \w{3} \d{4})\s+(\d{2} \w{3} \d{4})\s+(.+?)\s+([\d,]*\.\d{2})?\s+([\d,]*\.\d{2})?\s+([\d,]*\.\d{2})",
        re.MULTILINE,
    )

    matches = list(full_desc_pattern.finditer(combined_text))

    if not matches:
        st.error("⚠️ No transactions detected. Please check the regex pattern.")

    for match in matches:
        date, value_date, description, debit, credit, balance = match.groups()
        transactions.append([
            date.strip() if date else "",  
            value_date.strip() if value_date else "",  
            description.strip() if description else "",  
            float(debit.replace(',', '')) if debit else 0.00,  
            float(credit.replace(',', '')) if credit else 0.00,  
            float(balance.replace(',', '')) if balance else 0.00,  
        ])

    df = pd.DataFrame(transactions, columns=["Transaction Date", "Value Date", "Description", "Withdrawal (Dr)", "Deposit (Cr)", "Running Balance"])
    return df

# ---------------------------
# Streamlit UI
# ---------------------------
st.set_page_config(page_title="FAB PDF to Excel Converter", layout="wide")

st.title("FAB Bank Statement PDF Extractor")

# Upload PDF Files
uploaded_files = st.file_uploader("Upload FAB PDF Statements", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    all_transactions = []

    for uploaded_file in uploaded_files:
        pdf_bytes = io.BytesIO(uploaded_file.read())  # Convert file to BytesIO

        df = extract_fab_transactions(pdf_bytes)

        if not df.empty:
            all_transactions.append(df)

    if all_transactions:
        final_df = pd.concat(all_transactions, ignore_index=True)
        st.write("### Extracted Transactions")
        st.dataframe(final_df, use_container_width=True)

        # Download Button
        output = io.BytesIO()
        final_df.to_excel(output, index=False, engine="openpyxl")
        output.seek(0)

        st.download_button(
            label="⬇️ Download Extracted Transactions",
            data=output,
            file_name="FAB_Transactions.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("⚠️ No transactions found in the uploaded PDF.")
