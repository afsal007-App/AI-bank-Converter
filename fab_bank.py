import pdfplumber
import pandas as pd
import re
import io

# ---------------------------
# FAB Extraction Function
# ---------------------------
def extract_fab_transactions(pdf_bytes):
    transactions = []
    combined_text = ""

    pdf_bytes.seek(0)
    with pdfplumber.open(pdf_bytes) as pdf:
        combined_text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

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
# ✅ REQUIRED process() FUNCTION
# ---------------------------
def process(pdf_files):
    all_transactions = []

    for pdf_file in pdf_files:
        pdf_bytes = io.BytesIO(pdf_file.getvalue())  # Convert file to BytesIO
        df = extract_fab_transactions(pdf_bytes)

        if not df.empty:
            all_transactions.append(df)

    if all_transactions:
        return pd.concat(all_transactions, ignore_index=True)
    else:
        return pd.DataFrame(columns=["Transaction Date", "Value Date", "Description", "Withdrawal (Dr)", "Deposit (Cr)", "Running Balance"])
