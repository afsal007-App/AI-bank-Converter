import pdfplumber
import pandas as pd
import io
import streamlit as st

# Keywords that indicate unwanted header rows (to be removed)
header_keywords = ["Transaction Date", "Narration", "Debit", "Credit", "Running Balance"]

# Function to process a list of PDF files
def process(pdf_files):
    all_transactions = []

    # Process each uploaded PDF file
    for pdf_file in pdf_files:
        structured_data = []
        
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                table = page.extract_table()  # Extract table from the page
                
                if table:
                    for row in table:
                        # Ensure the row has enough data
                        if len(row) < 6:
                            continue

                        # Check if the row is a duplicate header and skip it
                        if any(header in row[0] for header in header_keywords) and "Running Balance" in row:
                            continue  # Skip this row

                        # Extract relevant columns and clean text
                        transaction_date = row[0].replace("\n", " ").strip()  # Remove newline & spaces
                        narration = row[2].replace("\n", " ").strip()  # Clean narration text

                        # Initialize Debit and Credit
                        debit = 0.0
                        credit = 0.0

                        # Extract Debit (Row index 3)
                        try:
                            if row[3] and row[3] != "0.00":  # Ensure it's not empty or zero
                                debit = float(row[3].replace(',', '').replace("\n", " ").strip())  
                        except ValueError:
                            debit = 0.0  
                        
                        # Extract Credit (Row index 4)
                        try:
                            if row[4] and row[4] != "0.0":  # Ensure it's not empty or zero
                                credit = float(row[4].replace(',', '').replace("\n", " ").strip())  
                        except ValueError:
                            credit = 0.0  

                        # Extract Running Balance (Row index 5)
                        running_balance = row[5].replace("\n", " ").strip() if len(row) > 5 else None

                        # Append structured row to data list
                        structured_data.append([transaction_date, narration, debit, credit, running_balance])

        all_transactions.extend(structured_data)  # Add extracted data to the master list

    # Convert combined data to DataFrame
    df_combined = pd.DataFrame(all_transactions, columns=["Transaction Date", "Narration", "Debit", "Credit", "Account Balance"])

    # Remove any additional remaining rows with headers
    df_combined = df_combined[df_combined["Transaction Date"] != "Transaction Date"]

    # Ensure "Account Balance" is treated as a string for comparison consistency
    df_combined["Account Balance"] = df_combined["Account Balance"].astype(str)

    # Convert "Transaction Date" column to datetime for sorting
    df_combined["Transaction Date"] = pd.to_datetime(df_combined["Transaction Date"], format="%d-%m-%Y", errors='coerce')

    # Drop any rows where the date conversion failed
    df_combined = df_combined.dropna(subset=["Transaction Date"])

    # List to store merged transactions
    merged_data = []
    prev_row = None

    for _, row in df_combined.iterrows():
        if prev_row is not None and row["Account Balance"] == prev_row["Account Balance"]:
            # Merge the narration and update debit/credit values
            prev_row["Narration"] += " " + row["Narration"]
            prev_row["Debit"] = max(prev_row["Debit"], row["Debit"])
            prev_row["Credit"] = max(prev_row["Credit"], row["Credit"])
        else:
            # Append the previous row before processing a new one
            if prev_row is not None:
                merged_data.append(prev_row)
            prev_row = row.copy()  # Store current row for comparison

    # Append the last processed row
    if prev_row is not None:
        merged_data.append(prev_row)

    # Convert merged data into a DataFrame
    df_final = pd.DataFrame(merged_data)

    # Sort transactions by date (oldest first)
    df_final = df_final.sort_values(by="Transaction Date", ascending=True)


def run():
    st.header("Emirates Islamic Bank PDF Processor")

    uploaded_files = st.file_uploader("Upload Emirates Islamic Bank statement PDFs", type="pdf", accept_multiple_files=True)

    if uploaded_files:
        st.info("Processing uploaded files...")
        df = process(uploaded_files)

        if df.empty:
            st.warning("No transactions found.")
        else:
            st.success("Transactions extracted successfully!")
            st.dataframe(df)

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv, "emirates_islamic_transactions.csv", "text/csv")


    # Remove duplicate rows based on the "Account Balance" column, keeping only the first occurrence
    df_final = df_final.drop_duplicates(subset=["Account Balance"], keep="first")

    return df_final
