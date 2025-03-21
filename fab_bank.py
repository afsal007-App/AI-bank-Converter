import re
import pandas as pd
from PyPDF2 import PdfReader
import io
import streamlit as st

def process(pdf_files, opening_balance=None):  # ✅ Now accepts opening_balance
    """
    Extracts transactions from FAB Bank statements, cleans the data, and returns a structured DataFrame.

    Args:
        pdf_files (list): List of BytesIO PDF files.
        opening_balance (float, optional): User-defined opening balance. If None, the first transaction balance is used.

    Returns:
        pd.DataFrame: Processed transaction data.
    """

    structured_transactions = []
    date_pattern = r"\d{2} \w{3} \d{4}"  # Format: 02 JAN 2024
    amount_pattern = r"\d{1,3}(?:,\d{3})*\.\d{2}"  # Format: 1,000.00

    # Unwanted phrases (headers, footers, and bank disclaimers to remove)
    unwanted_phrases = [
        "balance carried forward",
        "date value date description debit credit balance",
        "important: the bank must be notified",
        "absence of any notification",
        "account statement",
        "first abu dhabi bank",
        "we shall endeavor to get back",
        "currency aed iban",
    ]

    for pdf_file in pdf_files:
        pdf_reader = PdfReader(pdf_file)
        pypdf2_text = "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
        pypdf2_lines = pypdf2_text.split("\n")

        current_transaction = {"DATE": "", "VALUE DATE": "", "DESCRIPTION": ""}

        for line in pypdf2_lines:
            line = line.strip()
            dates = re.findall(date_pattern, line)

            if len(dates) == 2:
                if current_transaction["DATE"]:
                    structured_transactions.append(current_transaction.copy())

                current_transaction = {
                    "DATE": dates[0],
                    "VALUE DATE": dates[1],
                    "DESCRIPTION": line,
                }
            else:
                current_transaction["DESCRIPTION"] += " " + line

        if current_transaction["DATE"]:
            structured_transactions.append(current_transaction)

    df_final = pd.DataFrame(structured_transactions)

    if df_final.empty:
        return df_final  # Return empty DataFrame if no transactions were found

    # Function to clean description
    def clean_description(text):
        return re.sub(r"\s+", " ", text).strip()

    # Function to remove unwanted headers, footers, and extra information
    def remove_unwanted_text(text):
        text = text.lower()
        for phrase in unwanted_phrases:
            if phrase in text:
                return ""
        return text

    # Function to remove transaction dates from DESCRIPTION column
    def remove_dates_from_description(text):
        return re.sub(date_pattern, "", text).strip()

    # Function to extract amount and balance
    def extract_amounts(text):
        amounts = re.findall(amount_pattern, text)
        if len(amounts) >= 2:
            return amounts[0].replace(",", ""), amounts[1].replace(",", "")
        return "", ""

    # Apply cleaning functions
    df_final["DESCRIPTION"] = df_final["DESCRIPTION"].apply(clean_description)
    df_final["DESCRIPTION"] = df_final["DESCRIPTION"].apply(remove_unwanted_text)
    df_final["DESCRIPTION"] = df_final["DESCRIPTION"].apply(remove_dates_from_description)
    df_final = df_final[df_final["DESCRIPTION"] != ""]  # Remove empty descriptions

    # Extract Amount and Balance
    df_final[["AMOUNT", "BALANCE"]] = df_final["DESCRIPTION"].apply(lambda x: pd.Series(extract_amounts(x)))

    # Convert to numeric
    df_final["AMOUNT"] = pd.to_numeric(df_final["AMOUNT"], errors="coerce")
    df_final["BALANCE"] = pd.to_numeric(df_final["BALANCE"], errors="coerce")

    # Remove rows with "Old Account Number"
    df_final = df_final[~df_final["DESCRIPTION"].str.contains("old account number", case=False, na=False)]

    # **Determine Opening Balance**
    if opening_balance is None:
        opening_balance = df_final["BALANCE"].iloc[0] if not df_final.empty else 0  # ✅ Uses user-provided balance or first balance

    # Calculate Running Balance
    df_final["RUNNING BALANCE"] = df_final["BALANCE"].fillna(method='ffill')

    # Calculate Actual Amount
    df_final["ACTUAL AMOUNT"] = df_final["RUNNING BALANCE"].diff()
    df_final["ACTUAL AMOUNT"].iloc[0] = df_final["BALANCE"].iloc[0] - opening_balance  # ✅ Adjusts based on opening balance

    # **Rename "DATE" to "Transaction Date" before returning**
    df_final.rename(columns={"DATE": "Transaction Date"}, inplace=True)

    return df_final  # ✅ Returns processed transactions as DataFrame


def run():
    st.header("FAB Bank PDF Processor")

    uploaded_files = st.file_uploader("Upload one or more FAB Bank PDF statements", type="pdf", accept_multiple_files=True)
    opening_balance_input = st.text_input("Optional: Enter Opening Balance (leave blank to auto-calculate)")

    if uploaded_files:
        try:
            opening_balance = float(opening_balance_input) if opening_balance_input.strip() else None
        except ValueError:
            st.error("Invalid opening balance. Please enter a numeric value.")
            return

        st.info("Processing uploaded file(s)...")
        df = process(uploaded_files, opening_balance)

        if df.empty:
            st.warning("No transactions found in the uploaded PDF(s).")
        else:
            st.success("Transactions extracted successfully!")
            st.dataframe(df)

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv, "fab_bank_transactions.csv", "text/csv")
