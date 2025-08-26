# Natural Language → SQL Query Assistant

**Türkçe Doğal Dil Sorularından Güvenli SQL Üreten, Çalıştıran ve Sonuçları Görselleştiren Uygulama**

---

## Proje Hakkında

Bu proje, Türkçe doğal dilde sorulan sorulardan güvenli SQL sorguları üretir, DuckDB veya PostgreSQL üzerinde çalıştırır ve sonuçları tablo + grafik olarak görselleştirir.

**Örnek:**  

**Soru:**  
"Son 6 ayda şehir bazında toplam ciro nedir?"

**Otomatik SQL:**  
```sql
SELECT c.city, SUM(s.amount) AS total_amount
FROM sales AS s
JOIN customers AS c ON s.customer_id = c.customer_id
WHERE s.month >= '2024-02'
GROUP BY c.city
ORDER BY total_amount DESC
LIMIT 10;
```
---

**Sonuç:** Tablo + Bar Chart

---

## Özellikler

- ✅ Türkçe doğal dil → güvenli SQL dönüşümü  
- ✅ DuckDB üzerinde çalıştırma desteği  
- ✅ Guardrails ile güvenlik katmanı (DELETE, UPDATE, DROP vs. yasak)  
- ✅ Few-Shot Prompting → Örnekler üzerinden LLM destekli sorgu üretimi  
- ✅ OpenRouter (Gemma) desteği  
- ✅ Otomatik grafik seçimi (bar, line, stacked)  
- ✅ Streamlit arayüzü ile kolay kullanım  
- ✅ Sentetik veri üretimi → customers.csv, sales.csv  
- ✅ Goldset dosyası ile model doğruluk testi  

---

## Mimari

User - Streamlit UI (app.py)  
NL→SQL Motoru (nl2sql.py)  
Guardrails (guardrails.py)  
SQL Runner (runner.py)  
DuckDB / PostgreSQL  
Sonuç - Tablo + Grafik

### Bileşenler

- **UI (Streamlit):** Kullanıcıdan soru alır, sonucu gösterir.  
- **NL→SQL Motoru:** Few-shot prompt + LLM ile SQL üretir.  
- **Guardrails:** SQL’in güvenliğini kontrol eder.  
- **SQL Runner:** DuckDB/Postgres üzerinde sorguyu çalıştırır.  
- **Auto-Chart:** Sonuca göre grafik türünü otomatik seçer.  

---

## Klasör Yapısı

NATURAL-LANGUAGE-SQL/
- data/                     # Veri dosyaları
  - customers.csv           # Müşteri verisi
  - sales.csv               # Satış verisi
  - database.duckdb         # DuckDB veritabanı
  - goldset_v3.csv          # Test seti
  - schema.yaml             # Şema sözlüğü
- data_generator/
  - fake_data_generator.py  # Sentetik veri üretimi
  - goldset_creator.py      # Goldset oluşturan script
- app.py                    # Streamlit arayüzü
- nl2sql.py                 # NL→SQL motoru
- guardrails.py             # SQL güvenlik kontrolleri
- runner.py                 # SQL sorgularını çalıştıran modül
- requirements.txt          # Bağımlılıklar
- README.md                 # Proje dökümantasyonu

##  Kurulum ve Çalıştırma

```bash
# 1. Depoyu Klonla
git clone https://github.com/kullanici/natural-language-sql.git
cd natural-language-sql

# 2. Sanal Ortam Oluştur
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Gerekli Kütüphaneleri Yükle
pip install -r requirements.txt

# 4. .env Dosyasını Hazırla
# Dosya içine şu satırı ekleyin:
# OPENAI_API_KEY=senin_openrouter_api_keyin

# Uygulamayı Çalıştır
streamlit run app.py

# Tarayıcıda otomatik olarak http://localhost:8501 açılacak
```

## Guardrails & Güvenlik

- Sadece `SELECT` sorguları üretilir.  
- İzinli tablolar: `customers`, `sales`  
- İzinli kolonlar: `customer_id, city, segment, credit_tier, income, month, purchases, amount`  
- Yasaklı komutlar: `DELETE, UPDATE, DROP, ALTER, INSERT`  
- `LIMIT 1000` zorunlu → ağır sorguları engeller.  
- JOIN sadece `customers ↔ sales` arasında yapılabilir.  

---

## Otomatik Görselleştirme

- Zaman serisi → Line Chart  
- Kategori + Sayısal → Bar Chart  
- Tek sayısal değer → Bar Chart  

---

## Değerlendirme Metrikleri

| Metod               | Hedef        |
|--------------------|-------------|
| Syntactic Accuracy  | ≥ %95       |
| Execution Success   | ≥ %90       |
| Semantic Accuracy   | ≥ %85       |
| Latency (p95)       | ≤ 1.5sn     |
| UX Memnuniyeti      | ≥ 4/5       |

---

## Geliştirme Yol Haritası

- Few-shot NL→SQL motoru  
- Guardrails + şema kontrolü  
- DuckDB/Postgres desteği  
- Streamlit UI  
- Goldset ile doğruluk ölçümü  
- EXPLAIN planına göre otomatik optimizasyon  
- RAG entegrasyonu ile doğruluk artırma  
- Loglama + kullanıcı davranış analitiği  

---

## Yazar

**Nida Kayaduman**  
📧 kayaduman@sabanciuniv.edu
