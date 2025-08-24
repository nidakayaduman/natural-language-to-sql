import os
import openai
from dotenv import load_dotenv
from guardrails import validate_sql
from runner import run_query

# .env dosyasindaki API key'i yukle
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_base = "https://openrouter.ai/api/v1"

# Sistem mesaji
SYSTEM_PROMPT = """\
Sen yalnizca izinli sema uzerinde guvenli SQL SELECT sorgulari ureten bir NL→SQL yardimcisisin.
Kullanici Turkce sorular sorar, sen yalnizca SQL cevabi uretirsin. Aciklama yapma.
Izinli tablolar ve kolonlar:
- customers(customer_id, city, segment, credit_tier, income)
- sales(customer_id, month, purchases, amount)

Kurallar:
- Sadece SELECT sorgusu uret.
- LIMIT 1000 ekle (zorunlu).
- month alani YYYY-MM formatindadir.
- JOIN gerektiginde kullanilmalidir.
- Sorgunun sonunda ; olmalidir.
- Tarih filtrelerinde month alanina gore yil bazli filtre istenirken LIKE 'YYYY-%' kalibini kullan.
"""

# Ornek promptlar
FEW_SHOT_EXAMPLES = """
Kullanici: Son 6 ayda sehir bazinda toplam ciro nedir? Ilk 10'u sirala.
Assistant:
SELECT c.city, SUM(s.amount) AS total_amount
FROM sales s
JOIN customers c ON s.customer_id = c.customer_id
WHERE s.month >= '2024-03'
GROUP BY c.city
ORDER BY total_amount DESC
LIMIT 10;

Kullanici: Segment ve kredi skoruna gore ortalama sepet tutarini goster.
Assistant:
SELECT c.segment, c.credit_tier, AVG(s.amount) AS avg_basket
FROM sales s
JOIN customers c ON s.customer_id = c.customer_id
GROUP BY c.segment, c.credit_tier
LIMIT 1000;

Kullanici: Istanbul'daki musterilerin aylik ciro trendi nedir?
Assistant:
SELECT s.month, SUM(s.amount) AS total_amount
FROM sales s
JOIN customers c ON s.customer_id = c.customer_id
WHERE c.city = 'Istanbul'
GROUP BY s.month
ORDER BY s.month
LIMIT 1000;

Kullanici: Geliri 100 bin TL uzerindeki musterilerin ortalama alisveris sayisi nedir?
Assistant:
SELECT AVG(s.purchases) AS avg_purchases
FROM sales s
JOIN customers c ON s.customer_id = c.customer_id
WHERE c.income > 100000
LIMIT 1000;

Kullanici: Her sehirdeki musteri sayisi nedir?
Assistant:
SELECT city, COUNT(*) AS total_customers
FROM customers
GROUP BY city
ORDER BY total_customers DESC
LIMIT 1000;
"""

# Kullanicinin sorusunu prompt'a ekler
def build_prompt(user_question: str) -> str:
    return FEW_SHOT_EXAMPLES + f"\nKullanici: {user_question}\nAssistant:\n"

# OpenAI ile SQL uretir
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
