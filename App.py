import streamlit as st

# ==== Bank Modules ====
import Rak_Bank
import al_jazira_bank
import emirates_islamic_bank
import fab_bank
import Wio_bank

# ==== Bank Mapping ====
bank_modules = {
    "🏦 RAK Bank": Rak_Bank,
    "🏢 Al Jazira Bank": al_jazira_bank,
    "🕌 Emirates Islamic Bank": emirates_islamic_bank,
    "💳 FAB Bank": fab_bank,
    "🧾 WIO Bank": Wio_bank
}

# ==== Page Config ====
st.set_page_config(page_title="Bank PDF Extractor", layout="centered")

# ==== CSS Styling ====
st.markdown("""
    <style>
    .title {
        font-size: 3rem;
        font-weight: 900;
        text-align: center;
        padding-top: 1rem;
        background: linear-gradient(90deg, #00dbde, #fc00ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: glow 3s ease-in-out infinite alternate;
    }
    .subtext {
        text-align: center;
        font-size: 1.05rem;
        color: #aaa;
        margin-top: -10px;
        margin-bottom: 30px;
    }
    .glass-card {
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 20px;
        padding: 30px;
        margin-top: 30px;
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        transition: transform 0.3s ease;
    }
    .glass-card:hover {
        transform: scale(1.02);
        box-shadow: 0 15px 40px rgba(0, 0, 0, 0.25);
    }
    .dropdown-label {
        font-size: 1.2rem;
        font-weight: 600;
        color: #00dbde;
        margin-bottom: 12px;
    }
    hr {
        border: none;
        border-top: 1px solid rgba(255,255,255,0.1);
        margin: 40px 0;
    }
    @keyframes glow {
        from {
            text-shadow: 0 0 10px #00dbde, 0 0 20px #00dbde;
        }
        to {
            text-shadow: 0 0 20px #fc00ff, 0 0 30px #fc00ff;
        }
    }
    </style>
""", unsafe_allow_html=True)

# ==== Header ====
st.markdown("<div class='title'>Bank Statement PDF Extractor</div>", unsafe_allow_html=True)
st.markdown("<div class='subtext'>Convert your bank PDFs into clean, usable data 📄 ➡️ 📊</div>", unsafe_allow_html=True)

# ==== Glass Dropdown Section ====
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.markdown('<div class="dropdown-label">🔽 Select Your Bank</div>', unsafe_allow_html=True)
selected_bank = st.selectbox("", list(bank_modules.keys()))
st.markdown('</div>', unsafe_allow_html=True)

# ==== Divider ====
st.markdown("<hr>", unsafe_allow_html=True)

# ==== Launch Selected Bank Processor ====
if selected_bank:
    bank_modules[selected_bank].run()
