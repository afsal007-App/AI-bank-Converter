import streamlit as st
import pdfplumber
import pandas as pd
import io

# Streamlit page configuration
st.set_page_config(page_title="PDF Bank Statement Extractor", layout="wide")

# Function to process a single PDF file and extract transactions
def process_pdf(pdf_file):
    structured_data = []
    header_keywords = ["Transaction Date", "Narration", "Debit", "Credit", "Running Balance"]

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                for row in table:
                    if len(row) < 6:
                        continue  # Skip incomplete rows

                    # Skip header rows
                    if any(header in row[0] for header in header_keywords) and "Running Balance" in row:
                        continue

                    # Extract relevant columns
                    transaction_date = row[0].replace("\n", " ").strip()
                    narration = row[2].replace("\n", " ").strip()

                    debit, credit = 0.0, 0.0
                    try:
                        if row[3] and row[3] != "0.00":
                            debit = float(row[3].replace(',', '').replace("\n", " ").strip())
                    except ValueError:
                        pass

                    try:
                        if row[4] and row[4] != "0.0":
                            credit = float(row[4].replace(',', '').replace("\n", " ").strip())
                    except ValueError:
                        pass

                    running_balance = row[5].replace("\n", " ").strip() if len(row) > 5 else None
                    structured_data.append([transaction_date, narration, debit, credit, running_balance])

    return structured_data

# Streamlit UI
st.title("📄 PDF Bank Statement Extractor")

uploaded_files = st.file_uploader("Upload one or multiple PDF bank statements", type="pdf", accept_multiple_files=True)

if uploaded_files:
    all_transactions = []

    # Process each uploaded PDF
    for pdf_file in uploaded_files:
        transactions = process_pdf(pdf_file)
        all_transactions.extend(transactions)

    # Convert to DataFrame
    df = pd.DataFrame(all_transactions, columns=["Date", "Narration", "Debit", "Credit", "Account Balance"])

    # Remove header rows
    df = df[df["Date"] != "Transaction Date"]

    # Convert "Date" column to datetime format
    df["Date"] = pd.to_datetime(df["Date"], format="%d-%m-%Y", errors='coerce')

    # Drop invalid date rows
    df = df.dropna(subset=["Date"])

    # Merge transactions with the same running balance
    merged_data = []
    prev_row = None

    for _, row in df.iterrows():
        if prev_row is not None and row["Account Balance"] == prev_row["Account Balance"]:
            prev_row["Narration"] += " " + row["Narration"]
            prev_row["Debit"] = max(prev_row["Debit"], row["Debit"])
            prev_row["Credit"] = max(prev_row["Credit"], row["Credit"])
        else:
            if prev_row is not None:
                merged_data.append(prev_row)
            prev_row = row.copy()

    if prev_row is not None:
        merged_data.append(prev_row)

    # Convert back to DataFrame
    df_final = pd.DataFrame(merged_data)

    # Sort by date
    df_final = df_final.sort_values(by="Date", ascending=True)

    # Remove duplicate rows based on "Account Balance"
    df_final = df_final.drop_duplicates(subset=["Account Balance"], keep="first")

    # Show DataFrame in Streamlit
    st.write("### Extracted Transactions")
    st.dataframe(df_final)

    # Convert DataFrame to Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_final.to_excel(writer, index=False, sheet_name="Transactions")
    excel_data = output.getvalue()

    # Download button
    st.download_button(
        label="📥 Download Transactions as Excel",
        data=excel_data,
        file_name="Extracted_Transactions.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.info("Upload your bank statements in PDF format to extract transactions into an Excel file.")
