import streamlit as st
import importlib
import io
import sys
import os

# Ensure the current directory is in the system path
sys.path.append(os.path.dirname(__file__))

# Define available banks and their corresponding Python files
BANK_OPTIONS = {
    "Emirates Islamic Bank": "emirates_islamic_bank",
    "Al Jazira Bank": "al_jazira_bank",
    "FAB Bank": "fab_bank"
}

st.title("Bank Statement PDF Converter")

# Bank Selection
selected_bank = st.selectbox("Select Your Bank", list(BANK_OPTIONS.keys()))

# Upload PDF Files
uploaded_files = st.file_uploader("Upload Bank PDF Statements", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    pdf_paths = [io.BytesIO(file.getvalue()) for file in uploaded_files]

    # Dynamically import the correct processing script
    module_name = BANK_OPTIONS[selected_bank]

    try:
        bank_module = importlib.import_module(module_name)  # Import bank's module
        df_final = bank_module.process(pdf_paths)  # Run the `process()` function

        st.write("### Extracted Transactions")
        st.dataframe(df_final)

        # Allow CSV Download
        st.download_button(
            label="Download Extracted Transactions",
            data=df_final.to_csv(index=False).encode("utf-8"),
            file_name=f"{selected_bank.replace(' ', '_')}_Transactions.csv",
            mime="text/csv"
        )
    except ModuleNotFoundError:
        st.error(f"Processing script for {selected_bank} not found.")
    except AttributeError:
        st.error(f"The script {module_name}.py must contain a function `process(pdf_files)`.")
