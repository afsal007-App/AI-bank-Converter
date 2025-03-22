import streamlit as st
from streamlit_lottie import st_lottie
import requests

# ==== Bank Modules ====
import Rak_Bank
import al_jazira_bank
import emirates_islamic_bank
import fab_bank
import Wio_bank

# ==== Bank Mapping with Emoji Labels ====
bank_modules = {
    "🏦 RAK Bank": Rak_Bank,
    "🏢 Al Jazira Bank": al_jazira_bank,
    "🕌 Emirates Islamic Bank": emirates_islamic_bank,
    "💳 FAB Bank": fab_bank,
    "🧾 WIO Bank": Wio_bank
}

# ==== Load Lottie Animation ====
def load_lottie_url(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

lottie_icon = load_lottie_url("https://assets10.lottiefiles.com/packages/lf20_jyxd3gpv.json")  # Simple banking animation

# ==== Streamlit Page Config ====
st.set_page_config(page_title="Bank PDF Extractor", layout="centered")

# ==== Custom CSS Styling ====
st.markdown("""
    <style>
    /* Gradient Title */
    .title {
        font-size: 2.8rem;
        font-weight: 800;
        text-align: center;
        padding: 0.5em 0;
        background: linear-gradient(90deg, #00c6ff, #0072ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    /* Subtext under title */
    .subtext {
        text-align: center;
        font-size: 1.05rem;
        color: #ccc;
        margin-top: -10px;
        margin-bottom: 30px;
    }
    /* Glass Dropdown Container */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 30px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        transition: all 0.3s ease-in-out;
        margin-top: 30px;
    }
    .glass-card:hover {
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.15);
    }
    .dropdown-label {
        font-size: 1.2rem;
        font-weight: 600;
        color: #00c6ff;
        margin-bottom: 12px;
    }
    </style>
""", unsafe_allow_html=True)

# ==== Page Title ====
st.markdown("<div class='title'>Bank Statement PDF Extractor</div>", unsafe_allow_html=True)
st.markdown("<div class='subtext'>Convert your bank PDFs into clean, structured data 📄 ➡️ 📊</div>", unsafe_allow_html=True)

# ==== Lottie Animation ====
st_lottie(lottie_icon, height=150, key="bank_anim")

# ==== Dropdown Section in a Styled Card ====
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.markdown('<div class="dropdown-label">🔽 Select Your Bank</div>', unsafe_allow_html=True)
selected_bank = st.selectbox("", list(bank_modules.keys()))
st.markdown('</div>', unsafe_allow_html=True)

# ==== Run Selected Bank Module ====
if selected_bank:
    bank_modules[selected_bank].run()
