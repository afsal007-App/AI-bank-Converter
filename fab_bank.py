import pandas as pd
import re
from PyPDF2 import PdfReader
import io

# Function to extract transactions from a single PDF
def extract_transactions_from_pdf(pdf_file):
    pdf_reader = PdfReader(pdf_file)
    pypdf2_text = "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
    pypdf2_lines = pypdf2_text.split("\n")

    structured_transactions = []
    current_transaction = {"DATE": "", "VALUE DATE": "", "DESCRIPTION": ""}

    # Patterns for extracting dates and amounts
    date_pattern = r"\d{2} \w{3} \d{4}"  # Pattern for detecting valid dates (e.g., 02 JAN 2024)
    amount_pattern = r"\d{1,3}(?:,\d{3})*\.\d{2}"  # Pattern for detecting amounts (e.g., 1,000.00)

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

    for line in pypdf2_lines:
        line = line.strip()

        # Detect dates (First date -> DATE, Next date -> VALUE DATE)
        dates = re.findall(date_pattern, line)

        if len(dates) == 2:  # If two dates are found, it's a new transaction
            if current_transaction["DATE"]:  # Save previous transaction
                structured_transactions.append(current_transaction.copy())

            # Start a new transaction
            current_transaction = {
                "DATE": dates[0],
                "VALUE DATE": dates[1],
                "DESCRIPTION": line,
            }

        else:  # Merge remaining text into description
            current_transaction["DESCRIPTION"] += " " + line

    # Save the last transaction
    if current_transaction["DATE"]:
        structured_transactions.append(current_transaction)

    return structured_transactions

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

# Function to remove transaction dates from the DESCRIPTION column
def remove_dates_from_description(text):
    date_pattern = r"\d{2} \w{3} \d{4}"
    return re.sub(date_pattern, "", text).strip()

# Function to extract amount and balance
def extract_amounts(text):
    amount_pattern = r"\d{1,3}(?:,\d{3})*\.\d{2}"
    amounts = re.findall(amount_pattern, text)
    if len(amounts) >= 2:
        return amounts[0].replace(",", ""), amounts[1].replace(",", "")
    return "", ""

# Streamlit App
st.title("📄 PDF Transaction Extractor")

# File uploader (multiple PDFs)
uploaded_files = st.file_uploader("Upload one or more PDF files", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    all_transactions = []
    
    for pdf_file in uploaded_files:
        transactions = extract_transactions_from_pdf(pdf_file)
        all_transactions.extend(transactions)  # Merge into one list

    # Convert extracted transactions to DataFrame
    df_final = pd.DataFrame(all_transactions)

    if not df_final.empty:
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

        # Ask for an Opening Balance
        user_opening_balance = st.text_input("Enter Opening Balance (Leave blank to use first transaction's balance):")

        # Determine the opening balance
        if user_opening_balance:
            opening_balance = float(user_opening_balance)
        else:
            opening_balance = df_final["BALANCE"].iloc[0] if not df_final.empty else 0

        # Calculate Running Balance
        df_final["RUNNING BALANCE"] = df_final["BALANCE"].fillna(method='ffill')

        # Calculate Actual Amount
        df_final["ACTUAL AMOUNT"] = df_final["RUNNING BALANCE"].diff()
        df_final["ACTUAL AMOUNT"].iloc[0] = df_final["BALANCE"].iloc[0] - opening_balance  # First row adjustment

        # Save to Excel
        output_file = "Combined_Transactions.xlsx"
        df_final.to_excel(output_file, index=False)

        # Provide download link
        st.success("✅ Transactions processed successfully!")
        st.download_button("📥 Download Excel File", data=open(output_file, "rb"), file_name=output_file, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        # Display Data
        st.dataframe(df_final)

