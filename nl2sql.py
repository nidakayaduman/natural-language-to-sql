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
SYSTEM_PROMPT = """\
Sen yalnızca izinli şema üzerinde güvenli SQL SELECT sorguları üreten bir NL→SQL yardımcısısın.
Kullanıcı Türkçe sorular sorar, sen yalnızca SQL cevabı üretirsin. Açıklama yapma.

İzinli tablolar ve kolonlar:
- customers(customer_id, city, segment, credit_tier, income)
- sales(customer_id, month, purchases, amount)

Kurallar:
- Sadece SELECT sorgusu üret.
- LIMIT 1000 ekle (zorunlu).
- month alanı YYYY-MM formatındadır.
- JOIN gerektiginde kullanilmalidir.
- Sorgunun sonunda ; olmalı.
- Tarih filtrelerinde month alanına göre yıl bazlı filtre istenirken LIKE 'YYYY-%' kalıbını kullan.
- segment alanı YALNIZCA şu değerlerden biri olabilir: 'Bireysel', 'KOBI', 'Kurumsal'.
- Eğer kullanıcı başka bir şey derse, uygun Türkçe değeri otomatik eşleştir:
    'Corporate' → 'Kurumsal'
    'Individual' → 'Bireysel'
    'SME' → 'KOBI'
- credit_tier yalnızca 1, 2, 3, 4 veya 5 olabilir.
- income numeric tipindedir, string olarak kullanılmaz.
- Şema dışındaki hiçbir tablo veya kolon kullanılamaz.
- Kullanıcı bir şehir (city) belirtirse**, bu city mutlaka `WHERE` filtresine eklenmelidir.

"""

# Örnek few-shot prompt'lar
FEW_SHOT_EXAMPLES = """
Kullanici: Kurumsal musterilerin toplam harcamasını şehir bazında göster.
Assistant:
SELECT c.city, SUM(s.amount) AS total_spending
FROM sales s
JOIN customers c ON s.customer_id = c.customer_id
WHERE c.segment = 'Kurumsal'
GROUP BY c.city
ORDER BY total_spending DESC
LIMIT 1000;

Kullanici: KOBI musterilerin ortalama alışveriş tutarı nedir?
Assistant:
SELECT AVG(s.amount) AS avg_spending
FROM sales s
JOIN customers c ON s.customer_id = c.customer_id
WHERE c.segment = 'KOBI'
LIMIT 1000;

Kullanici: Bireysel musterilerin satın alma sayısını aylık bazda göster.
Assistant:
SELECT s.month, SUM(s.purchases) AS total_purchases
FROM sales s
JOIN customers c ON s.customer_id = c.customer_id
WHERE c.segment = 'Bireysel'
GROUP BY s.month
ORDER BY s.month
LIMIT 1000;
"""

# Prompt inşası
def build_prompt(user_question: str) -> str:
    return FEW_SHOT_EXAMPLES + f"\nKullanici: {user_question}\nAssistant:\n"

# SQL üretimi
def generate_sql(user_question: str, model_choice: str) -> str:
    try:
        detect_forbidden_keywords(user_question)
    except ValueError as e:
        return f"❌ Güvensiz soru: {e}"

    prompt = build_prompt(user_question)

    # Ollama modeli (Mistral veya LLaMA3)
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

    # OpenRouter modeli (Gemma)
    else:
        try:
            response = openai.ChatCompletion.create(
                model="google/gemma-3-12b-it:free",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
            sql = response["choices"][0]["message"]["content"].strip()
        except Exception as e:
            return f"❌ OpenRouter hatası: {e}"

    # Segment isimlerini düzelt
    sql = fix_segments(sql)

    # SQL güvenlik kontrolü
    try:
        validate_sql(sql)
    except ValueError as e:
        return f"❌ Geçersiz SQL: {e}"

    return sql

# Ana fonksiyon
def answer_user_question(user_question: str, model_choice: str):
    sql = generate_sql(user_question, model_choice)

    if sql.startswith("❌"):
        return sql, None

    runner = SQLRunner()
    try:
        df = runner.execute_query(sql)
        return sql, df
    finally:
        runner.close()
