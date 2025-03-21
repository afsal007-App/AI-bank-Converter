import streamlit as st
from streamlit_lottie import st_lottie
import requests

# Bank modules
import Rak_Bank
import al_jazira_bank
import emirates_islamic_bank
import fab_bank

# ---------------------- Lottie Animation Loader ----------------------
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# ---------------------- Bank Module Mapping ----------------------
bank_modules = {
    "🏦 RAK Bank": Rak_Bank,
    "🏢 Al Jazira Bank": al_jazira_bank,
    "🕌 Emirates Islamic Bank": emirates_islamic_bank,
    "💳 FAB Bank": fab_bank
}

# ---------------------- Page Configuration ----------------------
st.set_page_config(page_title="Bank PDF Converter", layout="centered")

# ---------------------- Page Styling ----------------------
st.markdown(
    """
    <style>
    .main {
        background: linear-gradient(to right, #fdfbfb, #ebedee);
    }
    .title-text {
        font-size: 3rem;
        font-weight: 700;
        background: -webkit-linear-gradient(45deg, #1e90ff, #00c9a7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .dropdown-label {
        font-size: 1.2rem;
        color: #444;
        font-weight: 500;
        margin-bottom: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------------- Title and Animation ----------------------
col1, col2 = st.columns([1, 2])
with col1:
    lottie_animation = load_lottieurl("https://assets4.lottiefiles.com/packages/lf20_w51pcehl.json")
    st_lottie(lottie_animation, height=180, key="bank_anim")
with col2:
    st.markdown("<div class='title-text'>✨ Smart Bank PDF Extractor</div>", unsafe_allow_html=True)
    st.write("Effortlessly extract transactions from your bank statements.")

st.divider()

# ---------------------- Bank Selection ----------------------
st.markdown("<div class='dropdown-label'>Select Your Bank:</div>", unsafe_allow_html=True)
selected_bank = st.selectbox("", list(bank_modules.keys()))

# ---------------------- Run Selected Bank Module ----------------------
if selected_bank:
    bank_modules[selected_bank].run()
