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
    "Emirates Islamic Bank": "emirates_islamic_bank",
    "Al Jazira Bank": "al_jazira_bank",
    "FAB Bank": "fab_bank"
}

st.title("🏦 Bank Statement PDF Converter")

# Bank Selection
selected_bank = st.selectbox("📌 Select Your Bank", list(BANK_OPTIONS.keys()))

# Upload PDF Files
uploaded_files = st.file_uploader(
    "📂 Upload Bank PDF Statements", type=["pdf"], accept_multiple_files=True
)

if uploaded_files:
    pdf_paths = [io.BytesIO(file.getvalue()) for file in uploaded_files]  # Convert uploaded files to BytesIO

    module_name = BANK_OPTIONS[selected_bank]

    try:
        # Import the corresponding bank processing module dynamically
        bank_module = importlib.import_module(module_name)

        # Ensure the module has a function named `process`
        if not hasattr(bank_module, "process"):
            st.error(f"❌ The script {module_name}.py must contain a function `process(pdf_files)`.")
        else:
            with st.spinner(f"⏳ Processing PDFs for {selected_bank}..."):
                df_final = bank_module.process(pdf_paths)  # Call the `process` function in the selected bank script

            if not df_final.empty:
                # Identify possible date columns dynamically
                possible_date_cols = ["Transaction Date", "DATE", "Value Date", "VALUE DATE"]
                date_col = next((col for col in df_final.columns if col in possible_date_cols), None)

                # ✅ Correct Date Parsing
                if date_col:
                    # Check if the date format needs conversion
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
