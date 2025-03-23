import fitz  # PyMuPDF
import re
import pandas as pd
import streamlit as st
from io import BytesIO

# Regex patterns
date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
reference_pattern = re.compile(r"\b\d{9,}-\d+\b")
amount_pattern = re.compile(r"\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?")
of_page_pattern = re.compile(r"^\d+\s+of\d+$")

page_stop_triggers = [
    "ﻭﻓﻰ ﺣﺎﻝ ﺇﻛﺘﺸﺎﻑ ﺃﻱ ﺧﻄﺄ",
    "Mashreqbank PSC is regulated by the Central Bank of the United Arab Emirates"
]

unwanted_line_keywords = [
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

def is_unwanted_line(line):
    if of_page_pattern.match(line):
        return True
    return any(keyword in line for keyword in unwanted_line_keywords)

def is_page_stop_trigger(line):
    return any(trigger in line for trigger in page_stop_triggers)

def extract_transaction_blocks(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    transactions = []
    current_txn = []

    for page in doc:
        lines = page.get_text().split("\n")
        stop = False
        for line in lines:
            stripped = line.strip()
            if not stripped or is_unwanted_line(stripped):
                continue
            if is_page_stop_trigger(stripped):
                stop = True
                break
            if date_pattern.match(stripped):
                if current_txn:
                    transactions.append(current_txn)
                    current_txn = []
                capture_date = stripped
            current_txn.append(stripped)
        if stop:
            continue
    if current_txn:
        transactions.append(current_txn)
    doc.close()
    return transactions

def parse_transaction_block(block):
    txn_date = block[0] if len(block) > 0 else ""
    value_date = block[1] if len(block) > 1 else ""

    narration_lines = block[2:] if len(block) > 2 else []
    narration = value_date + " " + " ".join(narration_lines)
    narration = re.sub(r"\b[A-Z]{3}\s\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?\b", "", narration)

    reference = ""
    for line in block:
        match = reference_pattern.search(line)
        if match:
            reference = match.group()
            break

    matches = amount_pattern.findall(narration)
    balance = matches[-1] if matches else ""

    return {
        "Date": txn_date,
        "Value Date": value_date,
        "Narration": narration.strip(),
        "Reference": reference,
        "Balance": balance
    }

def process_pdf(file):
    raw_txns = extract_transaction_blocks(file)
    structured = [parse_transaction_block(txn) for txn in raw_txns]
    df = pd.DataFrame(structured)
    df["Balance"] = df["Balance"].str.replace(",", "").astype(float, errors="ignore")
    return df

def run():
    st.header("Mashreq Bank Statement Parser")

    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
    if uploaded_file:
        with st.spinner("Processing..."):
            df = process_pdf(uploaded_file)
            st.success("Extraction completed!")

            st.dataframe(df[["Date", "Narration", "Balance"]])

            # Download CSV
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", data=csv, file_name="mashreq_statement.csv", mime="text/csv")

# For Main.py to call this function
if __name__ == "__main__":
    run()
