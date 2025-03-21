import streamlit as st

# Import individual bank modules
import Rak_Bank  # replace with actual filenames, no .py
import bank_abc  # another example

# Map for dropdown
bank_modules = {
    "Rak bank": Rak_Bank,
    "Bank ABC": bank_abc,
    # Add more banks here
}

st.title("Bank Statement PDF Extractor")

# Dropdown for selecting a bank
selected_bank = st.selectbox("Select a Bank", list(bank_modules.keys()))

# Run the selected bank's function
if selected_bank:
    bank_modules[selected_bank].run()
