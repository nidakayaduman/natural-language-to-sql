import os
import openai
from dotenv import load_dotenv
from guardrails import validate_sql, fix_segments  # fix_segments ekledik
from runner import SQLRunner

# .env dosyasindaki API key'i yukle
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_base = "https://openrouter.ai/api/v1"

# Sistem mesaji
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
"""

# Ornek promptlar
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

# Kullanıcı sorusunu prompt'a ekler
def build_prompt(user_question: str) -> str:
    return FEW_SHOT_EXAMPLES + f"\nKullanici: {user_question}\nAssistant:\n"

# OpenAI ile SQL üretir
def generate_sql(user_question: str) -> str:
    prompt = build_prompt(user_question)
    response = openai.ChatCompletion.create(
        model="google/gemma-3-12b-it:free",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    sql = response["choices"][0]["message"]["content"].strip()

    # Önce segment düzeltmesini uygula
    sql = fix_segments(sql)

    # Guardrails ile SQL doğrulaması
    try:
        validate_sql(sql)
    except ValueError as e:
        return f"❌ Geçersiz SQL: {e}"

    return sql


# Konsoldan soru alir
if __name__ == "__main__":
    while True:
        q = input("Soru (cikmak icin q): ")
        if q.lower() == "q":
            break
        sql = generate_sql(q)
        print("\nUretilen SQL:\n", sql)
        print("-" * 80)
