def extract_fab_transactions(pdf_bytes):
    transactions = []
    combined_text = ""

    pdf_bytes.seek(0)
    with pdfplumber.open(pdf_bytes) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                combined_text += text + "\n"

    # Debugging: Show raw extracted text
    st.write("📜 Extracted Text from PDF:", combined_text[:1000])  # Show first 1000 characters

    if not combined_text.strip():
        st.error("❌ No text was extracted from the PDF! This could mean it's a scanned image.")
        return pd.DataFrame()

    # Regex pattern for FAB bank transactions
    full_desc_pattern = re.compile(
        r"(\d{2} \w{3} \d{4})\s+(\d{2} \w{3} \d{4})\s+(.+?)\s+([\d,]*\.\d{2})?\s+([\d,]*\.\d{2})?\s+([\d,]*\.\d{2})",
        re.MULTILINE,
    )

    matches = list(full_desc_pattern.finditer(combined_text))

    if not matches:
        st.error("⚠️ No transactions were found using regex. The pattern may need adjustments.")

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
