import PyPDF2
import re
import pandas as pd
import os
import streamlit as st
from io import BytesIO

# Regex patterns
unwanted_phrases = [
     "Opening balance",
    "ﺍﻟﺘﺎﺭﻳﺦ",
    "ﺍﻟﻤﻌﺎﻣﻠﺔ",
    "ﺭﻗﻢ ﺍﻟﻤﺮﺟﻊ",
    "ﻗﻴﻮﺩ",
    "ﻗﻴﻮﺩ ﺩﺍﺋﻨﻪ",
    "ﺍﻟﺮﺻﻴﺪ",
    "page",
    "The items and balance shown",
    "of the statement date",
    "All charges, terms and conditions",
    "Please note that for foreign currency",
    "verified. Report any discrepancies",
    "accurate.",
    "indicative only",
    "ﺍﻟﺮﺟﺎﺀ ﺍﻟﺘﺄﻛﺪ ﻣﻦ ﺻﺤﺔ ﺍﻟﻤﻌﺎﻣﻼﺕ ﻭﺍﻟﻤﺒﺎﻟﻎ ﺍﻟﻤﺒﻴﻨﺔ ﻏﻰ ﻫﺬﺍ ﺍﻟﻜﺸﻒ",
    "Closing balance",
     "8 of 8",
]
of_pattern = re.compile(r'\bof\s*\d+\b', re.IGNORECASE)
date_pattern = re.compile(r'\b\d{4}-\d{2}-\d{2}(?=\D)', re.IGNORECASE)
amount_pattern = re.compile(r'\b(?:\d{1,3}(?:,\d{3})*|\d+)\.\d{1,2}\b|\b0\b')
header_pattern = re.compile(
    r'Date\s*Transaction\s*Reference\s*Number\s*Debit\s*Balance\s*Credit',
    re.IGNORECASE
)

# Functions
def extract_transactions(file_bytes):
    transactions = []
    current_transaction = []
    current_date = ""

    reader = PyPDF2.PdfReader(file_bytes)
    for page in reader.pages:
        text = page.extract_text()
        if text:
            lines = text.splitlines()
            for line in lines:
                line = line.strip()
                line = header_pattern.sub('', line)

                if any(phrase in line for phrase in unwanted_phrases) or of_pattern.search(line):
                    continue

                date_match = date_pattern.search(line)
                if date_match:
                    if current_transaction:
                        transactions.append((current_date, current_transaction))
                        current_transaction = []
                    current_date = date_match.group()
                    current_transaction.append(line)
                else:
                    current_transaction.append(line)

    if current_transaction:
        transactions.append((current_date, current_transaction))
    return transactions

def parse_structured_data(transactions):
    structured_data = []
    for date, lines in transactions:
        full_text = " ".join(lines).strip()
        all_amounts = amount_pattern.findall(full_text)
        balance = all_amounts[-1] if all_amounts else ""

        if balance:
            balance_index = full_text.rfind(balance)
            description = (full_text[:balance_index] + full_text[balance_index + len(balance):]).strip()
        else:
            description = full_text

        description = re.sub(r'\s+', ' ', description)

        structured_data.append({
            "Date": date,
            "Description": description,
            "Balance": balance
        })
    return structured_data

# Streamlit App
def run():
    st.title("📑 Multi-PDF Bank Statement Parser")

    opening_balance = st.number_input("Enter Opening Balance", value=0.00, step=0.01, format="%.2f")

    uploaded_files = st.file_uploader("Upload one or more PDF statements", type=["pdf"], accept_multiple_files=True)

    if uploaded_files:
        all_data = []

        for file in uploaded_files:
            st.info(f"📄 Processing: {file.name}")
            transactions = extract_transactions(file)
            structured_data = parse_structured_data(transactions)
            df = pd.DataFrame(structured_data)

            df = df[
                df['Date'].notna() &
                df['Balance'].notna() &
                (df['Date'].str.strip() != "") &
                (df['Balance'].str.strip() != "")
            ]

            df['Balance'] = df['Balance'].str.replace(",", "").astype(float)
            df['Amount'] = df['Balance'].diff()
            df.loc[df.index[0], 'Amount'] = df.loc[df.index[0], 'Balance'] - opening_balance
            df['Source_File'] = file.name

            all_data.append(df)

        final_df = pd.concat(all_data, ignore_index=True)
        final_df.reset_index(drop=True, inplace=True)

        st.success("✅ Parsing complete!")
        st.dataframe(final_df)

        # Download buttons
        csv = final_df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download CSV", csv, "combined_statements.csv", "text/csv")

        excel_io = BytesIO()
        final_df.to_excel(excel_io, index=False, engine='openpyxl')
        excel_io.seek(0)
        st.download_button("⬇️ Download Excel", excel_io, "combined_statements.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# For direct run
if __name__ == "__main__":
    run()
