import streamlit as st
import pandas as pd
from nl2sql import answer_user_question
from runner import SQLRunner

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
    .stButton:nth-of-type(1) button:hover,
    .stButton:nth-of-type(2) button:hover,
    .stButton:nth-of-type(3) button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 25px rgba(255, 110, 127, 0.4) !important;
        background: linear-gradient(135deg, #bfe9ff 0%, #764ba2 50%, #ff6e7f 100%) !important;
    }
    .stButton:nth-of-type(1) button:active,
    .stButton:nth-of-type(2) button:active,
    .stButton:nth-of-type(3) button:active {
        transform: translateY(-1px) !important;
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4) !important;
    }
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

st.markdown("<div class='title-text'>Chat With Nida's Bot</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle-text'>Verilerinizi anlamak için sorunuzu yazın. Sistem sizin yerinize gerekli analizi oluştursun.</div>", unsafe_allow_html=True)

# Model seçimi dropdown
st.markdown("### Model Seçimi")
model_choice = st.selectbox(
    "Kullanmak istediğiniz modeli seçin:",
    ["Gemma (OpenRouter)", "Mistral (Ollama)"]
)
st.session_state.model_choice = model_choice

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
user_input = st.text_area(
    "Sorunuzu yazın:", 
    height=90, 
    placeholder="Örn: İstanbul'daki KOBİ müşterilerin toplam harcamasını göster.", 
    value=st.session_state.user_input_value
)

# 🔹 Otomatik Grafik Seçimi Fonksiyonu
def auto_chart(df):
    try:
        # Eğer 'month' kolonunu içeriyorsa → line chart
        if "month" in df.columns:
            st.line_chart(df.set_index("month"))
            return

        # Kategorik + sayısal kolonları kontrol et
        category_cols = [col for col in df.columns if df[col].dtype == 'object']
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns

        # Eğer kategori + sayısal kolon varsa → bar chart
        if category_cols and len(numeric_cols) >= 1:
            st.bar_chart(df.set_index(category_cols[0])[numeric_cols[0]])
            return

        # Sadece tek sayısal kolon varsa → bar chart
        if len(numeric_cols) == 1:
            st.bar_chart(df[numeric_cols[0]])
            return

        # Çoklu sayısal kolon varsa → line chart
        if len(numeric_cols) > 1:
            st.line_chart(df[numeric_cols])
            return

    except Exception as e:
        st.warning(f"Grafik oluşturulamadı: {e}")

# Buton ve sonuç
if st.button("Cevabı Göster"):
    if not user_input.strip():
        st.warning("Lütfen bir soru girin.")
    else:
        with st.spinner("SQL üretiliyor ve çalıştırılıyor..."):
            try:
                generated_sql, result_df = answer_user_question(user_input, model_choice)
                st.session_state.generated_sql = generated_sql
                st.session_state.result_df = result_df
            except Exception as e:
                st.session_state.generated_sql = None
                st.session_state.result_df = None
                st.error(f"❌ Hata: {e}")

# 🔹 Sonucu gösterme kısmı (butondan ayrı)
if "generated_sql" in st.session_state:
    if st.session_state.result_df is None:
        st.markdown("### ❌ Hata Oluştu", unsafe_allow_html=True)
        st.error(st.session_state.generated_sql)
        if st.session_state.generated_sql:
            with st.expander("Teknik Hata Detayı"):
                st.code(st.session_state.generated_sql, language="text")
    else:
        # SQL'i göster
        st.markdown("<span style='color:#ff6e7f'><b>Oluşturulan SQL</b></span>", unsafe_allow_html=True)
        st.code(st.session_state.generated_sql, language="sql")

        # Tabloyu göster
        st.markdown("<span style='color:#0097a7'><b>Sonuç</b></span>", unsafe_allow_html=True)
        st.dataframe(st.session_state.result_df, use_container_width=True)

        # Otomatik grafik çiz
        auto_chart(st.session_state.result_df)

st.markdown("</div>", unsafe_allow_html=True)

# Logları Göster ve İndir
st.markdown("### Log Kayıtları")

if st.button("Logları Göster"):
    runner = SQLRunner()
    try:
        logs_df = runner.conn.execute("SELECT * FROM logs ORDER BY ts DESC").fetchdf()
        if logs_df.empty:
            st.info("Henüz hiç log kaydı yok.")
        else:
            st.dataframe(logs_df, use_container_width=True)

            # İndirme butonu
            csv_data = logs_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button(
                label="⬇Logları CSV olarak indir",
                data=csv_data,
                file_name="logs.csv",
                mime="text/csv"
            )
    except Exception as e:
        st.error(f"❌ Loglar alınamadı: {e}")
    finally:
        runner.close()
# Footer
st.markdown("""
<div class='footer'>
    Made with ❤️ by Nida
</div>
""", unsafe_allow_html=True)
