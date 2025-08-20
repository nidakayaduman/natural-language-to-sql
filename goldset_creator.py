import pandas as pd
import os

data = [
    {
        "question": "Son 6 ayda şehir bazında toplam ciro nedir? İlk 10’u sırala.",
        "expected_sql": "SELECT c.city, SUM(s.amount) AS total_amount FROM sales s JOIN customers c ON s.customer_id = c.customer_id WHERE s.month >= strftime('%Y-%m', date('now', '-6 months')) GROUP BY c.city ORDER BY total_amount DESC LIMIT 10;"
    },
    {
        "question": "Segment ve kredi skoruna göre ortalama sepet tutarını göster.",
        "expected_sql": "SELECT c.segment, c.credit_tier, AVG(s.amount) AS avg_basket FROM sales s JOIN customers c ON s.customer_id = c.customer_id GROUP BY c.segment, c.credit_tier LIMIT 1000;"
    },
    {
        "question": "İstanbul’daki müşterilerin aylık ciro trendi nedir?",
        "expected_sql": "SELECT s.month, SUM(s.amount) AS total_amount FROM sales s JOIN customers c ON s.customer_id = c.customer_id WHERE c.city = 'Istanbul' GROUP BY s.month ORDER BY s.month LIMIT 1000;"
    },
    {
        "question": "Geliri 100 bin TL üzerindeki müşterilerin ortalama alışveriş sayısı nedir?",
        "expected_sql": "SELECT AVG(s.purchases) AS avg_purchases FROM sales s JOIN customers c ON s.customer_id = c.customer_id WHERE c.income > 100000 LIMIT 1000;"
    },
    {
        "question": "Tier 4 ve 5 müşterilerin segment bazında en çok harcama yaptığı ilk 3 şehri göster.",
        "expected_sql": "SELECT c.city, c.segment, SUM(s.amount) AS total_spending FROM sales s JOIN customers c ON s.customer_id = c.customer_id WHERE c.credit_tier IN (4, 5) GROUP BY c.city, c.segment ORDER BY total_spending DESC LIMIT 3;"
    },
    {
        "question": "2023 yılında toplam alışveriş sayısı nedir?",
        "expected_sql": "SELECT SUM(s.purchases) FROM sales s WHERE s.month LIKE '2023-%' LIMIT 1000;"
    },
    {
        "question": "Antalya’daki müşterilerin ortalama geliri ne kadar?",
        "expected_sql": "SELECT AVG(income) FROM customers WHERE city = 'Antalya' LIMIT 1000;"
    },
    {
        "question": "Her segmentin toplam harcama tutarı nedir?",
        "expected_sql": "SELECT c.segment, SUM(s.amount) FROM sales s JOIN customers c ON s.customer_id = c.customer_id GROUP BY c.segment LIMIT 1000;"
    },
    {
        "question": "Aylara göre toplam ciro değişimi nedir?",
        "expected_sql": "SELECT s.month, SUM(s.amount) FROM sales s GROUP BY s.month ORDER BY s.month LIMIT 1000;"
    },
    {
        "question": "2024 yılında İstanbul'daki toplam alışveriş sayısı kaç?",
        "expected_sql": "SELECT SUM(s.purchases) FROM sales s JOIN customers c ON s.customer_id = c.customer_id WHERE c.city = 'Istanbul' AND s.month LIKE '2024-%' LIMIT 1000;"
    },
    {
        "question": "En yüksek ortalama harcamaya sahip 5 şehir nedir?",
        "expected_sql": "SELECT c.city, AVG(s.amount) AS avg_spending FROM sales s JOIN customers c ON s.customer_id = c.customer_id GROUP BY c.city ORDER BY avg_spending DESC LIMIT 5;"
    },
    {
        "question": "Geliri 120.000 TL üstü olan müşterilerin şehir dağılımı nedir?",
        "expected_sql": "SELECT city, COUNT(*) AS customer_count FROM customers WHERE income > 120000 GROUP BY city ORDER BY customer_count DESC LIMIT 1000;"
    },
    {
        "question": "Ankara’daki Tier 5 müşterilerin ortalama harcaması nedir?",
        "expected_sql": "SELECT AVG(s.amount) FROM sales s JOIN customers c ON s.customer_id = c.customer_id WHERE c.city = 'Ankara' AND c.credit_tier = 5 LIMIT 1000;"
    },
    {
        "question": "Her şehirdeki müşteri sayısı nedir?",
        "expected_sql": "SELECT city, COUNT(*) AS total_customers FROM customers GROUP BY city ORDER BY total_customers DESC LIMIT 1000;"
    },
    {
        "question": "Aylık ortalama alışveriş sayısı nedir?",
        "expected_sql": "SELECT s.month, AVG(s.purchases) AS avg_purchases FROM sales s GROUP BY s.month ORDER BY s.month LIMIT 1000;"
    },
    {
        "question": "Her segmentin yıllık toplam ciroyu 2024 için göster.",
        "expected_sql": "SELECT c.segment, SUM(s.amount) FROM sales s JOIN customers c ON s.customer_id = c.customer_id WHERE s.month LIKE '2024-%' GROUP BY c.segment LIMIT 1000;"
    },
    {
        "question": "Geliri en yüksek 10 müşterinin şehir ve segment bilgisi nedir?",
        "expected_sql": "SELECT city, segment, income FROM customers ORDER BY income DESC LIMIT 10;"
    },
    {
        "question": "Tier 1 müşterilerin toplam alışveriş adedi nedir?",
        "expected_sql": "SELECT SUM(s.purchases) FROM sales s JOIN customers c ON s.customer_id = c.customer_id WHERE c.credit_tier = 1 LIMIT 1000;"
    },
    {
        "question": "2023 yılında toplam kaç müşteri alışveriş yaptı?",
        "expected_sql": "SELECT COUNT(DISTINCT s.customer_id) FROM sales s WHERE s.month LIKE '2023-%' LIMIT 1000;"
    },
    {
        "question": "İzmir'deki müşterilerin ortalama kredi skoru kaçtır?",
        "expected_sql": "SELECT AVG(credit_tier) FROM customers WHERE city = 'Izmir' LIMIT 1000;"
    },
    {
        "question": "Her kredi skoru için ortalama harcama ne kadar?",
        "expected_sql": "SELECT c.credit_tier, AVG(s.amount) FROM sales s JOIN customers c ON s.customer_id = c.customer_id GROUP BY c.credit_tier ORDER BY c.credit_tier LIMIT 1000;"
    },
    {
        "question": "Müşterilerin yaşadığı şehir ve gelir ortalamasını sırala.",
        "expected_sql": "SELECT city, AVG(income) AS avg_income FROM customers GROUP BY city ORDER BY avg_income DESC LIMIT 1000;"
    },
    {
        "question": "2024'ün her ayında segment bazlı toplam ciroyu göster.",
        "expected_sql": "SELECT s.month, c.segment, SUM(s.amount) FROM sales s JOIN customers c ON s.customer_id = c.customer_id WHERE s.month LIKE '2024-%' GROUP BY s.month, c.segment ORDER BY s.month LIMIT 1000;"
    },
    {
        "question": "100 bin TL altı gelire sahip müşterilerin segment dağılımı nedir?",
        "expected_sql": "SELECT segment, COUNT(*) FROM customers WHERE income < 100000 GROUP BY segment ORDER BY COUNT(*) DESC LIMIT 1000;"
    },
    {
        "question": "Her müşterinin toplam alışveriş adedini ve harcamasını listele.",
        "expected_sql": "SELECT customer_id, SUM(purchases) AS total_purchases, SUM(amount) AS total_amount FROM sales GROUP BY customer_id LIMIT 1000;"
    }
]

DATA_DIR = os.path.join(os.getcwd(), "data")
os.makedirs(DATA_DIR, exist_ok=True)

df = pd.DataFrame(data)
df.to_csv(os.path.join(DATA_DIR, "goldset_v1.csv"), index=False)

