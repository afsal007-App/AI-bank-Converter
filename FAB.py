import streamlit as st
import pdfplumber
import pandas as pd
import re
import io

# ---------------------------
# FAB Extraction Function (Streamlit-Compatible)
# ---------------------------
def extract_fab_transactions(pdf_bytes):
    transactions = []
    combined_text = ""

    pdf_bytes.seek(0)
    with pdfplumber.open(pdf_bytes) as pdf:
        combined_text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

    # Debugging: Show raw extracted text
    st.write("📜 Extracted Text (FAB):", combined_text[:1000])  # Display first 1000 characters

    # FAB transaction regex pattern
    full_desc_pattern = re.compile(
        r"(\d{2} \w{3} \d{4})\s+(\d{2} \w{3} \d{4})\s+(.+?)\s+([\d,]*\.\d{2})?\s+([\d,]*\.\d{2})?\s+([\d,]*\.\d{2})",
        re.MULTILINE,
    )

    matches = list(full_desc_pattern.finditer(combined_text))

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
        st.dataframe(final_df)

        # Download Button
        st.download_button(
            label="Download Transactions as CSV",
            data=final_df.to_csv(index=False).encode("utf-8"),
            file_name="FAB_Transactions.csv",
            mime="text/csv"
        )
    else:
        st.warning("⚠️ No transactions found in the uploaded PDF.")
