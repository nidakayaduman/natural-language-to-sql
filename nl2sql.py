import os
import openai
import requests
from dotenv import load_dotenv
from guardrails import validate_sql, fix_segments, detect_forbidden_keywords
from runner import SQLRunner


# .env dosyasındaki API key'i yükle
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_base = "https://openrouter.ai/api/v1"

# Ollama API endpoint
OLLAMA_URL = "http://localhost:11434/api/chat"

# Sistem mesajı
SYSTEM_PROMPT = """
Sen yalnızca izinli şema üzerinde güvenli SQL SELECT sorguları üreten bir NL→SQL yardımcısısın.
Kullanıcı Türkçe sorular sorar, sen yalnızca SQL cevabı üretirsin. Açıklama veya yorum yapma.

İzinli tablolar ve kolonlar:
- customers(customer_id, city, segment, credit_tier, income)
- sales(customer_id, month, purchases, amount)

Kurallar:
- Sadece SELECT sorgusu üret, başka SQL komutları yasaktır.
- Her SELECT sorgusunun sonunda mutlaka LIMIT 1000 olmalı.
- Eğer kullanıcı LIMIT belirtirse onu uygula, aksi halde LIMIT 1000 ekle.
- month alanı YYYY-MM formatında bir stringtir.
- Yıl filtresi yaparken YEAR() fonksiyonu kullanma; bunun yerine:
    SUBSTR(month, 1, 4) = 'YYYY'
- Ay filtresi yaparken SUBSTR(month, 6, 2) kullan.
- Eğer tarih aralığı sorulursa BETWEEN kullanabilirsin:
    SUBSTR(month, 1, 7) BETWEEN '2023-01' AND '2023-06'
- JOIN gerekiyorsa yalnızca customers ve sales tabloları arasında yapılmalı.
- SELECT’te agregasyon fonksiyonu (SUM, AVG, COUNT, MIN, MAX) ve normal kolonlar birlikte kullanılıyorsa,
  ilgili kolonlar mutlaka GROUP BY ifadesinde yer almalı.
- GROUP BY içinde alias değil, orijinal tablo.kolon adı kullanılmalı. Örnek:
    GROUP BY c.customer_id  ✅ DOĞRU
    GROUP BY musteri_id     ❌ YANLIŞ
- Eğer sorguda sadece agregasyon varsa GROUP BY gerekmez.
- segment alanı yalnızca şu değerlerden biri olabilir: 'Bireysel', 'KOBI', 'Kurumsal'.
- Kullanıcı başka dilde veya eş anlamlı değer girerse otomatik eşleştir:
    'Corporate' → 'Kurumsal'
    'Individual' → 'Bireysel'
    'SME' → 'KOBI'
- credit_tier yalnızca 1, 2, 3, 4 veya 5 olabilir.
- income numeric tipindedir, string olarak kullanılmaz.
- Şema dışındaki hiçbir tablo veya kolon kullanılamaz.
- Kullanıcı bir şehir (city) belirtirse, bu city mutlaka WHERE filtresine eklenmelidir.
- Eğer kullanıcı segment belirtmezse segment filtresi koyma.
- İngilizce segment isimlerini asla kullanma.
- Sorgunun sonunda mutlaka noktalı virgül (;) olmalı.
"""


# Örnek few-shot prompt'lar
FEW_SHOT_EXAMPLES = """
Kurumsal musterilerin toplam harcamasını şehir bazında göster.
SELECT c.city, SUM(s.amount) AS total_spending
FROM sales AS s
JOIN customers AS c ON s.customer_id = c.customer_id
WHERE c.segment = 'Kurumsal'
GROUP BY c.city
ORDER BY total_spending DESC
LIMIT 1000;

2023 yılında yapılan toplam satışları getir.
SELECT SUM(s.amount) AS total_sales
FROM sales AS s
WHERE SUBSTR(s.month, 1, 4) = '2023'
LIMIT 1000;

KOBI musterilerin ortalama alışveriş tutarı nedir?
SELECT AVG(s.amount) AS avg_spending
FROM sales AS s
JOIN customers AS c ON s.customer_id = c.customer_id
WHERE c.segment = 'KOBI'
LIMIT 1000;

Bireysel musterilerin satın alma sayısını aylık bazda göster.
SELECT s.month, SUM(s.purchases) AS total_purchases
FROM sales AS s
JOIN customers AS c ON s.customer_id = c.customer_id
WHERE c.segment = 'Bireysel'
GROUP BY s.month
ORDER BY s.month ASC
LIMIT 1000;

Her müşterinin toplam harcamasını getir.
SELECT c.customer_id, SUM(s.amount) AS total_spending
FROM sales AS s
JOIN customers AS c ON s.customer_id = c.customer_id
GROUP BY c.customer_id
ORDER BY total_spending DESC
LIMIT 1000;
"""

# Prompt inşası
def build_prompt(user_question: str) -> str:
    return FEW_SHOT_EXAMPLES + f"\nKullanici: {user_question}\nAssistant:\n"

def generate_sql(user_question: str, model_choice: str) -> str:
    try:
        detect_forbidden_keywords(user_question)
    except ValueError as e:
        return f"❌ Güvensiz ifade: {e}"

    prompt = build_prompt(user_question)

    # Ollama
    if model_choice in ["Mistral (Ollama)"]:
        model_name = "mistral" if "Mistral" in model_choice else "llama3"
        try:
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    "stream": False
                }
            )
            data = response.json()
            sql = data["message"]["content"].strip()
        except Exception as e:
            return f"❌ Ollama hatası: {e}"

    # OpenRouter
    else:
        try:
            response = openai.ChatCompletion.create(
                model="google/gemma-3-27b-it:free",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
            sql = response["choices"][0]["message"]["content"].strip()
        except Exception as e:
            import traceback
            detailed_error = traceback.format_exc()
            return f"❌ OpenRouter hatası:\n\n{detailed_error}"



    sql = fix_segments(sql)

    try:
        validate_sql(sql)
    except ValueError as e:
        return f"❌ SQL doğrulama hatası: {e}"

    return sql

# Ana fonksiyon
def answer_user_question(user_question: str, model_choice: str):
    sql = generate_sql(user_question, model_choice)

    if isinstance(sql, str) and sql.startswith("❌"):
        return sql, None

    runner = SQLRunner()
    try:
        df = runner.execute_query(sql)
        return sql, df
    finally:
        runner.close()
