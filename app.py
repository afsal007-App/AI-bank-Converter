import streamlit as st
import pdfplumber
import pytesseract
import pandas as pd
import re
from pdf2image import convert_from_path
from PIL import Image
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

# Function to extract text from scanned PDFs using OCR
def extract_text_from_scanned_pdf(pdf_path):
    images = convert_from_path(pdf_path)
    text = ""
    for img in images:
        text += pytesseract.image_to_string(img) + "\n"
    return text

# Function to parse extracted text into structured format
def parse_text(text):
    transactions = []
    lines = text.split("\n")
    for line in lines:
        match = re.search(r'(\d{2}/\d{2}/\d{4})\s+(.+)\s+(-?\d+\.\d{2})', line)
        if match:
            date, description, amount = match.groups()
            transactions.append({
                'Date': date,
                'Description': description.strip(),
                'Amount': float(amount)
            })
    return pd.DataFrame(transactions)

# Function to classify transactions
def train_transaction_classifier(data):
    vectorizer = TfidfVectorizer()
    X_train, X_test, y_train, y_test = train_test_split(data['Description'], data['Category'], test_size=0.2, random_state=42)
    model = make_pipeline(TfidfVectorizer(), MultinomialNB())
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    print(f'Classification Accuracy: {accuracy_score(y_test, predictions)}')
    return model

# Streamlit UI
st.title("Bank Statement PDF Converter")

uploaded_file = st.file_uploader("Upload your bank statement (PDF)", type=["pdf"])
if uploaded_file is not None:
    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    st.text("Extracting data...")
    text = extract_text_from_pdf("temp.pdf")
    df = parse_text(text)
    
    st.dataframe(df)
    
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", csv, "bank_statement.csv", "text/csv", key='download-csv')

# Main entry point
if __name__ == "__main__":
    st.sidebar.header("PDF Bank Statement Converter")
    st.sidebar.text("Upload a bank statement PDF to extract and categorize transactions.")
