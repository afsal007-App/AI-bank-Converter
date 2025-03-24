import pdfplumber
import pandas as pd
import streamlit as st
from io import BytesIO

expected_headers = [
    "Posting Date", "Value Date", "Description", "Ref/Cheque No",
    "Debit Amount", "Credit Amount", "Balance"
]

def extract_transactions_from_pdf(file):
    all_data = []
    header_found = False
    header_index = []

    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    clean_row = [cell.strip() if isinstance(cell, str) else "" for cell in row]

                    if not header_found and set(expected_headers).issubset(set(clean_row)):
                        header_found = True
                        header_index = [clean_row.index(col) for col in expected_headers]
                        continue

                    elif header_found:
                        if set(expected_headers).issubset(set(clean_row)):
                            continue
                        if len(clean_row) >= max(header_index) + 1:
                            selected_row = [clean_row[i] for i in header_index]
                            all_data.append(selected_row)
    return all_data

def run():
    #st.markdown("Bank PDF Processor")
    st.subheader("Bank PDF Processor")
    st.markdown("Upload **ADCB Bank PDF statements**")

    uploaded_files = st.file_uploader(
        "Upload PDF files",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )

    if not uploaded_files:
        st.info("📂 Please upload one or more PDF files.")
        return

    combined_data = []

    for file in uploaded_files:
        st.info(f"🔍 Processing: {file.name}")
        transactions = extract_transactions_from_pdf(file)
        combined_data.extend(transactions)

    df = pd.DataFrame(combined_data, columns=expected_headers)
    df.dropna(how='all', inplace=True)
    df.reset_index(drop=True, inplace=True)

    st.success("✅ Extraction complete!")
    st.dataframe(df)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download CSV", csv, "adcb_transactions.csv", "text/csv")

# For standalone run
if __name__ == "__main__":
    run()
