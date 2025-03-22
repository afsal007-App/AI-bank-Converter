import streamlit as st
from streamlit_lottie import st_lottie
import requests

# Bank Modules
import Rak_Bank
import al_jazira_bank
import emirates_islamic_bank
import fab_bank
import fab_bank

# Mapping
bank_modules = {
    "RAK Bank 🏦": Rak_Bank,
    "Al Jazira Bank 🏢": al_jazira_bank,
    "Emirates Islamic Bank 🕌": emirates_islamic_bank,
    "FAB Bank 💳": fab_bank
}

# Page Setup
st.set_page_config(page_title="Bank PDF Extractor", layout="centered")

# --- Styling ---
st.markdown("""
    <style>
    .title {
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
        padding: 0.5em 0;
        background: -webkit-linear-gradient(45deg, #0072ff, #00c6ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .subtext {
        text-align: center;
        font-size: 1rem;
        color: #444;
        margin-top: -15px;
        margin-bottom: 30px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("<div class='title'>Bank Statement PDF Extractor</div>", unsafe_allow_html=True)
st.markdown("<div class='subtext'>Convert your bank PDFs into clean, usable data 📄 ➡️ 📊</div>", unsafe_allow_html=True)

# --- Dropdown ---
selected_bank = st.selectbox("🔽 Select Your Bank", list(bank_modules.keys()))

# --- Launch ---
if selected_bank:
    bank_modules[selected_bank].run()
