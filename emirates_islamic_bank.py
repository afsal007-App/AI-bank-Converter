import pdfplumber
import pandas as pd
import os

# Folder containing PDF files (update this with your folder path)
pdf_folder = "/content/sample_data/Bank Statement - Emirates"  # Replace with your folder path
output_excel = "Combined_Transaction_Data.xlsx"

# List to store all transactions from multiple PDFs
all_transactions = []

# Keywords that indicate unwanted header rows (to be removed)
header_keywords = ["Transaction Date", "Narration", "Debit", "Credit", "Running Balance"]

# Function to process a single PDF file and extract transactions
def process_pdf(pdf_path):
    structured_data = []
    
    with pdfplumber.open(pdf_path) as pdf:
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

    return structured_data

# Process all PDFs in the folder
for file in os.listdir(pdf_folder):
    if file.lower().endswith(".pdf"):  # Process only PDF files
        pdf_path = os.path.join(pdf_folder, file)
        transactions = process_pdf(pdf_path)
        all_transactions.extend(transactions)  # Add extracted data to the master list

# Convert combined data to DataFrame
df_combined = pd.DataFrame(all_transactions, columns=["Date", "Narration", "Debit", "Credit", "Account Balance"])

# Remove any additional remaining rows with headers
df_combined = df_combined[df_combined["Date"] != "Transaction Date"]

# Ensure "Account Balance" is treated as a string for comparison consistency
df_combined["Account Balance"] = df_combined["Account Balance"].astype(str)

# Convert "Date" column to datetime for sorting (handling potential errors)
df_combined["Date"] = pd.to_datetime(df_combined["Date"], format="%d-%m-%Y", errors='coerce')

# Drop any rows where the date conversion failed
df_combined = df_combined.dropna(subset=["Date"])

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
df_final = df_final.sort_values(by="Date", ascending=True)

# Remove duplicate rows based on the "Account Balance" column, keeping only the first occurrence
df_final = df_final.drop_duplicates(subset=["Account Balance"], keep="first")

# Save the cleaned and merged data to an Excel file
df_final.to_excel(output_excel, index=False)

# Display success message
print(f"✅ All transactions have been extracted, merged, sorted by date, duplicates removed, and saved in '{output_excel}'.")
