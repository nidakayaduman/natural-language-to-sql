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
    
    /* Ana buton stili (Cevabı Göster) */
    .stButton button {
        background: linear-gradient(to right, #ff6e7f, #bfe9ff);
        color: black;
        font-weight: 600;
        border-radius: 10px;
        padding: 0.7rem 1.6rem;
        font-size: 1rem;
        border: none;
    }
    
    /* Örnek butonlar için özel stil */
    .stButton:nth-of-type(1) button,
    .stButton:nth-of-type(2) button,
    .stButton:nth-of-type(3) button {
        background: linear-gradient(135deg, #ff6e7f 0%, #764ba2 50%, #bfe9ff 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        font-size: 0.85rem !important;
        border: none !important;
        width: 100% !important;
        min-height: 80px !important;
        max-height: 80px !important;
        white-space: normal !important;
        line-height: 1.2 !important;
        text-align: center !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(255, 110, 127, 0.2) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    /* Hover efekti */
    .stButton:nth-of-type(1) button:hover,
    .stButton:nth-of-type(2) button:hover,
    .stButton:nth-of-type(3) button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 25px rgba(255, 110, 127, 0.4) !important;
        background: linear-gradient(135deg, #bfe9ff 0%, #764ba2 50%, #ff6e7f 100%) !important;
    }
    
    /* Active efekti */
    .stButton:nth-of-type(1) button:active,
    .stButton:nth-of-type(2) button:active,
    .stButton:nth-of-type(3) button:active {
        transform: translateY(-1px) !important;
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4) !important;
    }
    
    /* Ana buton (Cevabı Göster) için ayrı stil */
    .stButton:nth-of-type(4) button {
        background: linear-gradient(to right, #ff6e7f, #bfe9ff) !important;
        color: black !important;
        font-weight: 600 !important;
        border-radius: 10px !important;
        padding: 0.7rem 1.6rem !important;
        font-size: 1rem !important;
        border: none !important;
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

# Örnek Sorgu Butonları
st.markdown("#### Örnek Sorgular")
col1, col2, col3 = st.columns(3)

if "user_input_value" not in st.session_state:
    st.session_state.user_input_value = ""

with col1:
    if st.button("Ankara Bireysel"):
        st.session_state.user_input_value = "Ankara'daki bireysel müşterilerin toplam harcaması"

with col2:
    if st.button("6 Ayda En Çok Harcayan Şehir"):
        st.session_state.user_input_value = "Son 6 ayda en çok harcama yapan şehir hangisi?"

with col3:
    if st.button("Kurumsal Harcama Dağılımı"):
        st.session_state.user_input_value = "Kurumsal müşterilerin şehir bazlı harcama dağılımını göster"

# Kullanıcı girişi
user_input = st.text_area("Sorunuzu yazın:", height=90, placeholder="Örn: İstanbul'daki KOBİ müşterilerin toplam harcamasını göster.", value=st.session_state.user_input_value)

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