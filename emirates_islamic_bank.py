import pdfplumber
import PyPDF2
import fitz  # PyMuPDF
import pandas as pd
import io
import re
import ipywidgets as widgets
from IPython.display import display
from google.colab import files
from google.colab.data_table import DataTable  # Interactive preview

# Regular expression to match transaction entries (horizontal format)
transaction_pattern_horizontal = re.compile(
    r"(\d{2}-\d{2}-\d{4})\s+(\d{2}-\d{2}-\d{4})\s+(.+?)\s+([\d,]+\.\d{2})?\s+([\d,]+\.\d{2})?\s+([\d,]+\.\d{2})?"
)

# Function to extract text using PyPDF2
def extract_text_pypdf2(pdf_bytes):
    text = ""
    pdf_bytes.seek(0)  # Reset the BytesIO position
    reader = PyPDF2.PdfReader(pdf_bytes)
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

# Function to extract text using PyMuPDF (fitz)
def extract_text_pymupdf(pdf_bytes):
    text = ""
    pdf_bytes.seek(0)  # Reset the BytesIO position
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    for page in doc:
        text += page.get_text("text") + "\n"
    return text

# Function to extract text using pdfplumber
def extract_text_pdfplumber(pdf_bytes):
    text = ""
    pdf_bytes.seek(0)  # Reset the BytesIO position
    with pdfplumber.open(pdf_bytes) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

# Function to extract transactions from text (horizontal format)
def extract_transactions_horizontal(text):
    transactions = []
    lines = text.split("\n")

    for i in range(len(lines)):
        match = transaction_pattern_horizontal.match(lines[i])
        if match:
            transaction_date = match.group(1).strip()
            value_date = match.group(2).strip()
            narration = match.group(3).strip()
            debit_amount = match.group(4) or "0.00"
            credit_amount = match.group(5) or "0.00"
            running_balance = match.group(6) or "0.00"
            transactions.append([transaction_date, value_date, narration, debit_amount, credit_amount, running_balance])

    return transactions

# Function to extract transactions using a vertical method (table-based)
def extract_transactions_vertical(pdf_bytes):
    transactions = []
    pdf_bytes.seek(0)  # Reset the BytesIO position
    with pdfplumber.open(pdf_bytes) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                for row in table:
                    if len(row) >= 6:  # Ensure it's a valid transaction row
                        transactions.append(row)

    return transactions

# Function to process multiple PDFs
def process_pdfs(pdf_files):
    all_transactions = []

    for pdf_file in pdf_files:
        # Try extracting text using multiple methods
        text_pypdf2 = extract_text_pypdf2(pdf_file)
        text_pymupdf = extract_text_pymupdf(pdf_file)
        text_pdfplumber = extract_text_pdfplumber(pdf_file)

        # Choose the longest extracted text (most complete)
        text = max([text_pypdf2, text_pymupdf, text_pdfplumber], key=len)

        # Extract transactions using horizontal method
        transactions_horizontal = extract_transactions_horizontal(text)

        # Extract transactions using vertical method
        transactions_vertical = extract_transactions_vertical(pdf_file)

        # Combine results
        all_transactions.extend(transactions_horizontal)
        all_transactions.extend(transactions_vertical)

    # Create DataFrame
    columns = ["Transaction Date", "Value Date", "Narration", "Debit Amount", "Credit Amount", "Running Balance"]
    df = pd.DataFrame(all_transactions, columns=columns)

    # Remove duplicate header rows
    df = df[df["Transaction Date"] != "Value Date"]

    # Remove blank or missing transaction date rows
    df = df.dropna(subset=["Transaction Date"])
    df = df[df["Transaction Date"].str.strip() != ""]

    # Convert Transaction Date to datetime and sort
    df["Transaction Date"] = pd.to_datetime(df["Transaction Date"], format="%d-%m-%Y", errors="coerce")
    df = df.sort_values(by="Transaction Date", ascending=True)

    return df

# Upload multiple PDF files
uploaded_files = files.upload()

# Process all uploaded PDFs
pdf_paths = [io.BytesIO(uploaded_files[file]) for file in uploaded_files]
df_final = process_pdfs(pdf_paths)

# Remove blank rows from "Transaction Date" column
df_final_cleaned = df_final.dropna(subset=["Transaction Date"]).reset_index(drop=True)

# Display the cleaned DataFrame interactively
DataTable(df_final_cleaned)

# Save cleaned DataFrame as CSV
csv_filename = "Final_Cleaned_Transactions.csv"
df_final_cleaned.to_csv(csv_filename, index=False)

# Create Download Button
def download_file(b):
    files.download(csv_filename)

download_button = widgets.Button(description="Download Final Cleaned Transactions")
download_button.on_click(download_file)
display(download_button)
