import streamlit as st

# Import each individual bank module
import Rak_Bank
import al_jazira_bank
import emirates_islamic_bank
import fab_bank

# Mapping between dropdown label and corresponding module
bank_modules = {
    "RAK Bank": Rak_Bank,
    "Al Jazira Bank": al_jazira_bank,
    "Emirates Islamic Bank": emirates_islamic_bank,
    "FAB Bank": fab_bank
}

# Streamlit App Layout
st.set_page_config(page_title="Bank PDF Converter", layout="centered")
st.title("🏦 Bank Statement PDF Extractor")

# Dropdown to select bank
selected_bank = st.selectbox("Select Your Bank", list(bank_modules.keys()))

# Run selected bank's Streamlit function
if selected_bank:
    bank_modules[selected_bank].run()
