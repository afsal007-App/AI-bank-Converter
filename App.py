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

# Load Lottie animation
def load_lottie_url(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

lottie_icon = load_lottie_url("https://assets2.lottiefiles.com/packages/lf20_fcfjwiyb.json")  # Bank icon animation

# Page Setup
st.set_page_config(page_title="Bank PDF Extractor", layout="centered")

# --- Custom Styling ---
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
    .styled-dropdown {
        background-color: #f0f8ff;
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        margin: 20px 0;
        transition: 0.3s ease-in-out;
    }
    .styled-dropdown:hover {
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
    }
    .styled-dropdown h4 {
        font-size: 1.2rem;
        color: #333;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Page Header ---
st.markdown("<div class='title'>Bank Statement PDF Extractor</div>", unsafe_allow_html=True)
st.markdown("<div class='subtext'>Convert your bank PDFs into clean, structured data 📄 ➡️ 📊</div>", unsafe_allow_html=True)

# --- Animation ---
st_lottie(lottie_icon, height=120, key="bank_icon")

# --- Styled Dropdown Section ---
st.markdown('<div class="styled-dropdown"><h4>🔽 Select Your Bank</h4>', unsafe_allow_html=True)
selected_bank = st.selectbox("", list(bank_modules.keys()))
st.markdown('</div>', unsafe_allow_html=True)

# --- Run Selected Bank Module ---
if selected_bank:
    bank_modules[selected_bank].run()
