import streamlit as st
import importlib
import io
import sys
import os
import pandas as pd

# Ensure the current directory is in the system path
sys.path.append(os.path.dirname(__file__))

# Define available banks and their corresponding Python files
BANK_OPTIONS = {
    "Emirates Islamic Bank": {"module": "emirates_islamic_bank", "requires_opening_balance": False},
    "Al Jazira Bank": {"module": "al_jazira_bank", "requires_opening_balance": False},
    "FAB Bank": {"module": "fab_bank", "requires_opening_balance": True}  # ✅ FAB Bank supports opening balance
}

st.title("🏦 Bank Statement PDF Converter")

# Bank Selection
selected_bank = st.selectbox("📌 Select Your Bank", list(BANK_OPTIONS.keys()))

# Check if the selected bank requires an opening balance
requires_opening_balance = BANK_OPTIONS[selected_bank]["requires_opening_balance"]

# Upload PDF Files
uploaded_files = st.file_uploader(
    "📂 Upload Bank PDF Statements", type=["pdf"], accept_multiple_files=True
)

# Show opening balance input only if the bank requires it
opening_balance = None
if requires_opening_balance:
    opening_balance_input = st.text_input("💰 Enter Opening Balance (Leave blank to auto-detect)")
    if opening_balance_input:
        try:
            opening_balance = float(opening_balance_input)
        except ValueError:
            st.warning("⚠️ Please enter a valid number for the opening balance.")

if uploaded_files:
    pdf_paths = [io.BytesIO(file.getvalue()) for file in uploaded_files]  # Convert uploaded files to BytesIO

    module_name = BANK_OPTIONS[selected_bank]["module"]

    try:
        # Import the corresponding bank processing module dynamically
        bank_module = importlib.import_module(module_name)

        # Ensure the module has a function named `process`
        if not hasattr(bank_module, "process"):
            st.error(f"❌ The script {module_name}.py must contain a function `process(pdf_files, opening_balance)`.")
        else:
            with st.spinner(f"⏳ Processing PDFs for {selected_bank}..."):
                df_final = bank_module.process(pdf_paths, opening_balance)  # Pass opening balance if applicable

            if not df_final.empty:
                # Identify possible date columns dynamically
                possible_date_cols = ["Transaction Date", "DATE", "Value Date", "VALUE DATE"]
                date_col = next((col for col in df_final.columns if col in possible_date_cols), None)

                # ✅ Correct Date Parsing
                if date_col:
                    df_final[date_col] = pd.to_datetime(df_final[date_col], errors="coerce", dayfirst=True)
                    df_final = df_final.sort_values(by=date_col).reset_index(drop=True)
                    df_final[date_col] = df_final[date_col].dt.strftime("%d-%m-%Y")  # Convert to "dd-mm-yyyy"

                st.write(f"### 📊 Extracted Transactions for {selected_bank}")
                st.dataframe(df_final)

                # Allow CSV Download
                csv_data = df_final.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Download Extracted Transactions",
                    data=csv_data,
                    file_name=f"{selected_bank.replace(' ', '_')}_Transactions.csv",
                    mime="text/csv",
                )
            else:
                st.warning("⚠️ No transactions found in the uploaded PDFs.")

    except ModuleNotFoundError:
        st.error(f"❌ Processing script for **{selected_bank}** not found.")
    except Exception as e:
        st.error(f"🚨 An error occurred while processing: {str(e)}")
