import streamlit as st
from streamlit_lottie import st_lottie
import requests

# Bank Modules
import Rak_Bank
import al_jazira_bank
import emirates_islamic_bank
import fab_bank
import Wio_bank

# Mapping
bank_modules = {
    "RAK Bank 🏦": Rak_Bank,
    "Al Jazira Bank 🏦": al_jazira_bank,
    "Emirates Islamic Bank 🏦": emirates_islamic_bank,
    "FAB Bank 💳": fab_bank,
    "WIO Bank 🧾": Wio_bank
}

# Load Lottie animation (optional)
def load_lottie_url(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

lottie_icon = load_lottie_url("https://assets2.lottiefiles.com/packages/lf20_fcfjwiyb.json")  # Bank icon

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
    .dropdown-box {
        background-color: #f2f7ff;
        border-radius: 15px;
        padding: 30px 25px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        margin-bottom: 30px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("<div class='title'>Bank Statement PDF Extractor</div>", unsafe_allow_html=True)
st.markdown("<div class='subtext'>Convert your bank PDFs into clean, usable data 📄 ➡️ 📊</div>", unsafe_allow_html=True)

# --- Animation ---
st_lottie(lottie_icon, height=120, key="bank_icon")

# --- Styled Dropdown Section ---
st.markdown("<div class='dropdown-box'>", unsafe_allow_html=True)
selected_bank = st.selectbox("🔽 Choose Your Bank to Begin", list(bank_modules.keys()))
st.markdown("</div>", unsafe_allow_html=True)

# --- Launch Selected Bank Module ---
if selected_bank:
    bank_modules[selected_bank].run()
