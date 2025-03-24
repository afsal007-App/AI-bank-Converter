import streamlit as st
import PyPDF2
import re
import pandas as pd
from io import BytesIO

# Step 1: Extract cleaned lines
def extract_clean_lines(pdf_file):
    unwanted_phrases = [
        "Important:", "*T&Cs Apply", "600  52  5500", "First Abu Dhabi Bank PJSC",
        "We shall endeavor", "KHALID MOHAMED OBAID", "P.O.BOX 35566",
        "United Arab EmiratesAC-NUM", "IBAN", "Old Account Number",
        "Account Statement FROM", "Sheet no", "Balance brought forward"
    ]
    lines = []
    reader = PyPDF2.PdfReader(pdf_file)
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            for line in page_text.splitlines():
                if not any(phrase in line for phrase in unwanted_phrases):
                    clean = re.sub(r'\s+', ' ', line.strip())
                    if clean:
                        lines.append(clean)
    return lines

# Step 2: Check if line is start of transaction
def is_transaction_start(line):
    return re.match(r"^\d{1,2} \w{3} \d{4}\s+\d{1,2} \w{3} \d{4}", line) is not None

# Step 3: Group lines into transactions
def group_transactions(lines):
    transactions = []
    current = []
    for line in lines:
        if is_transaction_start(line):
            if current:
                transactions.append(current)
                current = []
        current.append(line)
    if current:
        transactions.append(current)
    return transactions

# Step 4: Extract date & description
def extract_date_and_description(block):
    first_line = block[0]
    match = re.match(r"^(\d{1,2} \w{3} \d{4})\s+(\d{1,2} \w{3} \d{4})\s+(.*)", first_line)
    if match:
        date = match.group(1)
        value_date = match.group(2)
        desc = match.group(3)
    else:
        date_matches = re.findall(r"\d{1,2} \w{3} \d{4}", first_line)
        if len(date_matches) >= 2:
            date = date_matches[0]
            value_date = date_matches[1]
            start = first_line.find(value_date) + len(value_date)
            desc = first_line[start:].strip()
        else:
            date = value_date = ""
            desc = first_line

    full_description = desc + " " + " ".join(block[1:])
    return {
        "Date": date,
        "Value Date": value_date,
        "Description": full_description.strip()
    }

# Step 5: Extract amount & balance
def extract_amount_balance_from_description(description):
    matches = re.findall(r'(?<!\d)(-?\d{1,3}(?:,\d{3})*\.\d{2})(?!\s*%)', description)
    if len(matches) >= 2:
        amount = matches[0].replace(',', '')
        balance = matches[1].replace(',', '')
    elif len(matches) == 1:
        amount = matches[0].replace(',', '')
        balance = ''
    else:
        amount = balance = ''
    return pd.Series([amount, balance])

# Step 6: Process single PDF
def process_pdf(pdf_file, filename="uploaded.pdf"):
    lines = extract_clean_lines(pdf_file)
    blocks = group_transactions(lines)
    data = [extract_date_and_description(block) for block in blocks]
    df = pd.DataFrame(data)
    df['Source File'] = filename

    # Filter out unwanted header-like rows
    df['Description_clean'] = df['Description'].str.replace(r'\s+', ' ', regex=True).str.strip().str.lower()
    df = df[~df['Description_clean'].str.contains("date value date description debit credit balance")]
    df.drop(columns=['Description_clean'], inplace=True)

    df[['Amount', 'Balance']] = df['Description'].apply(extract_amount_balance_from_description)
    return df

# Step 7: Streamlit run function
def run():
    #st.header("Bank PDF Processor")
    st.subheader("Bank PDF Processor")

    uploaded_files = st.file_uploader("Upload FAB Bank PDF statements", type="pdf", accept_multiple_files=True)
    opening_balance_input = st.text_input("Enter Opening Balance (leave blank to auto-calculate)")

    if uploaded_files:
        try:
            opening_balance = float(opening_balance_input) if opening_balance_input.strip() else None
        except ValueError:
            st.error("Opening balance must be numeric.")
            return

        all_dfs = []
        for file in uploaded_files:
            st.write(f"📄 Processing: {file.name}")
            df = process_pdf(file, file.name)
            all_dfs.append(df)

        if all_dfs:
            final_df = pd.concat(all_dfs, ignore_index=True)

            final_df['Balance'] = pd.to_numeric(final_df['Balance'], errors='coerce')
            final_df['Extracted Amount'] = final_df['Balance'].diff()
            if opening_balance is not None and not final_df.empty:
                final_df.loc[0, 'Extracted Amount'] = final_df.loc[0, 'Balance'] - opening_balance

            final_df['Extracted Amount'] = final_df['Extracted Amount'].round(2)

            st.success("✅ Transactions Extracted")
            st.dataframe(final_df)

            csv = final_df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv, "fab_transactions.csv", "text/csv")
        else:
            st.warning("⚠️ No valid transactions found.")
