import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Chat With Nida's Bot",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Stil tanımı
st.markdown("""
    <style>
    html, body, [class*="css"]  {
        background-color: #fdfcfb;
        font-family: 'Segoe UI', sans-serif;
    }
    .main {
        background-color: #ffffff;
        padding: 2rem;
        border-radius: 16px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
        max-width: 720px;
        margin: 2rem auto;
    }
    .title-text {
        background: linear-gradient(to right, #ff6e7f, #bfe9ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0.2rem;
    }
    .subtitle-text {
        font-size: 1.1rem;
        color: #606060;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stTextArea > div > textarea {
        background-color: #f9f9f9;
        border: 1px solid #cfcfcf;
        border-radius: 8px;
        padding: 0.75rem;
        font-size: 1rem;
    }
    .stButton button {
        background: linear-gradient(to right, #ff6e7f, #bfe9ff);
        color: black;
        font-weight: 600;
        border-radius: 10px;
        padding: 0.7rem 1.6rem;
        font-size: 1rem;
        border: none;
    }
    .stDataFrame {
        font-size: 0.95rem;
    }
    .footer {
        text-align: center;
        color: #999;
        margin-top: 3rem;
        font-size: 0.8rem;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='main'>", unsafe_allow_html=True)

st.markdown("<div class='title-text'>Chat With Nida</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle-text'>Verilerinizi anlamak için sorunuzu yazın. Sistem sizin yerinize gerekli analizi oluştursun.</div>", unsafe_allow_html=True)

# Kullanıcı girişi
user_input = st.text_area("Sorunuzu yazın:", height=90, placeholder="Örn: İstanbul’daki KOBİ müşterilerin toplam harcamasını göster.")

# Buton ve sonuç
display_sql = """SELECT city, segment, SUM(amount)
FROM sales
JOIN customers USING(customer_id)
WHERE city = 'Istanbul' AND segment = 'KOBI'
GROUP BY city, segment;"""

if st.button("Cevabı Göster"):
    if not user_input.strip():
        st.warning("Lütfen bir soru girin.")
    else:
        st.markdown("<span style='color:#ff6e7f'><b>Oluşturulan SQL</b></span>", unsafe_allow_html=True)
        st.code(display_sql, language="sql")

        st.markdown("<span style='color:#0097a7'><b>Sonuç</b></span>", unsafe_allow_html=True)
        dummy_result = pd.DataFrame({
            "Şehir": ["Istanbul"],
            "Müşteri Tipi": ["KOBI"],
            "Toplam Harcama": [193280.40]
        })
        st.dataframe(dummy_result, use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown("""
<div class='footer'>
    Made with ❤️ by Nida | NL → SQL MVP v1
</div>
""", unsafe_allow_html=True)
