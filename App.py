import streamlit as st

# Import individual bank modules
import Rak_Bank  # replace with actual filenames, no .py
import al_jazira_bank  # another example
import emirates_islamic_bank  # another example
import fab_bank  # another example

# Map for dropdown
bank_modules = {
    "RAK bank": Rak_Bank,
    "AL JAZIRA Bank": al_jazira_bank,
    "EMIRATES ISLAMIC BANK": emirates_islamic_bank,
    "FAB BANK": fab_bank,
    # Add more banks here
}

st.title("Bank Statement PDF Extractor")

# Dropdown for selecting a bank
selected_bank = st.selectbox("Select a Bank", list(bank_modules.keys()))

# Run the selected bank's function
if selected_bank:
    bank_modules[selected_bank].run()
