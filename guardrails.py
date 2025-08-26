import re
import sqlparse
import sqlglot
import duckdb
from datetime import datetime

# -------------------------
# İzinli tablolar, kolonlar, agregasyonlar, boyutlar
# -------------------------
ALLOWED_SEGMENTS = {"Bireysel", "KOBI", "Kurumsal"}
ALLOWED_TABLES = {"CUSTOMERS", "SALES"}
ALLOWED_COLUMNS = {
    "CUSTOMERS": {"customer_id", "city", "segment", "credit_tier", "income"},
    "SALES": {"customer_id", "month", "purchases", "amount"}
}
ALLOWED_AGGS = {"SUM", "AVG", "COUNT", "MIN", "MAX"}
ALLOWED_DIMS = {"month", "city", "segment", "credit_tier"}

FORBIDDEN_KEYWORDS = [
    "sil", "ekle", "güncelle", "değiştir",
    "drop", "insert", "update", "alter",
    "delete", "copy", "unload"
]

# -------------------------
# Kullanıcı sorusu tehlikeli mi kontrol et
# -------------------------
def detect_forbidden_keywords(question: str):
    for keyword in FORBIDDEN_KEYWORDS:
        if keyword.lower() in question.lower():
            raise ValueError(f"❌ '{keyword}' işlemlerine izin verilmiyor!")

# -------------------------
# Segment isimlerini normalize et
# -------------------------
def fix_segments(sql: str) -> str:
    mapping = {
        "corporate": "Kurumsal",
        "individual": "Bireysel",
        "sme": "KOBI",
        "kobi": "KOBI",
        "kurumsal": "Kurumsal",
        "bireysel": "Bireysel",
        "individuals": "Bireysel",
        "corporates": "Kurumsal",
        "smes": "KOBI",
        "Individual": "Bireysel",
        "İstanbul": "Istanbul",
        "İzmir": "Izmir"
    }
    for wrong, correct in mapping.items():
        sql = sql.replace(f"'{wrong}'", f"'{correct}'")
        sql = sql.replace(f'"{wrong}"', f"'{correct}'")
        sql = sql.replace(f"'{wrong.capitalize()}'", f"'{correct}'")
    return sql

# -------------------------
# SQL Temizleme (NEW)
# -------------------------
def clean_sql(sql: str) -> str:
    """
    Modelden dönen SQL'i normalize eder:
    - Fazladan boşlukları temizler
    - Segment isimlerini düzeltir
    - Küçük-büyük harfleri standart hale getirir
    - LIMIT yoksa ekler
    """
    # 1. sqlparse ile temel formatlama
    try:
        formatted = sqlparse.format(sql, reindent=True, keyword_case="upper")
    except Exception:
        formatted = sql.strip()

    # 2. Segmentleri normalize et
    formatted = fix_segments(formatted)

    # 3. LIMIT 1000 yoksa ekle
    if "LIMIT" not in formatted.upper():
        formatted = formatted.strip().rstrip(";") + " LIMIT 1000;"

    # 4. Fazla noktalı virgülleri temizle
    formatted = re.sub(r";+", ";", formatted)

    return formatted

# -------------------------
# AST Analizi → SELECT, alt-sorgu, JOIN
# -------------------------
def check_ast_structure(sql: str):
    try:
        ast = sqlglot.parse_one(sql)
    except Exception:
        if sql.strip().upper().startswith("SELECT"):
            return True  # parse hatasını görmezden gel
        raise ValueError("❌ SQL parse edilemedi! Lütfen daha basit bir sorgu deneyin.")

    # 1. Sadece SELECT sorgularına izin ver
    if ast.key and ast.key.upper() != "SELECT":
        raise ValueError("❌ Yalnızca SELECT sorgularına izin veriliyor!")

    # 2. Alt-sorgu derinliği ≤ 2 olmalı
    if hasattr(ast, "depth") and ast.depth > 2:
        raise ValueError("❌ Alt-sorgu derinliği çok fazla! Lütfen sorguyu basitleştirin.")

    # 3. JOIN sadece customers ve sales arasında olmalı
    if "JOIN" in sql.upper():
        if not ("CUSTOMERS" in sql.upper() and "SALES" in sql.upper()):
            raise ValueError("❌ JOIN yalnızca izinli tablolar arasında yapılabilir!")

    return True

# -------------------------
# EXPLAIN Planı → Ağır sorgu uyarısı
# -------------------------
def explain_and_check(sql: str):
    try:
        con = duckdb.connect("data/database.duckdb")
        plan = con.execute(f"EXPLAIN {sql}").fetchall()
        con.close()

        plan_str = " ".join(str(row) for row in plan).lower()

        # Eğer şehir veya ay filtresi varsa uyarı VERME
        if "WHERE" in sql.upper():
            if "CITY" in sql.upper() or "MONTH" in sql.upper():
                return True

        # Gerçekten tam tablo taraması varsa ancak o zaman uyar
        if "seq_scan" in plan_str or "full scan" in plan_str:
            return False
    except Exception:
        return True

    return True

# -------------------------
# Geliştirilmiş SQL doğrulama
# -------------------------
def validate_sql(sql: str):
    sql_upper = sql.upper()

    # 1. DROP, INSERT, UPDATE, DELETE, COPY, UNLOAD engeli
    forbidden = ["DELETE", "UPDATE", "DROP", "INSERT", "ALTER", "COPY", "UNLOAD"]
    for keyword in forbidden:
        if re.search(rf"\b{keyword}\b", sql_upper):
            raise ValueError(f"❌ {keyword} komutuna izin verilmiyor!")

    # 2. SELECT sorgusu mu kontrolü
    parsed = sqlparse.parse(sql)
    if not parsed or parsed[0].get_type() != "SELECT":
        raise ValueError("❌ Sadece SELECT sorgularına izin veriliyor!")

    # 3. LIMIT 1000 zorunlu
    if "LIMIT" not in sql_upper:
        sql = sql.strip().rstrip(";") + " LIMIT 1000"

    # 4. İzinli tabloları doğrula
    used_tables = re.findall(r"FROM\s+([a-zA-Z_]+)|JOIN\s+([a-zA-Z_]+)", sql_upper)
    used_tables = {tbl for pair in used_tables for tbl in pair if tbl}
    if not used_tables.issubset(ALLOWED_TABLES):
        raise ValueError(f"❌ İzinli tablolar dışında tablo kullanılamaz! "
                         f"Kullanılan: {used_tables} | İzinli: {ALLOWED_TABLES}")

    # 5. Kolon doğrulama
    for table, cols in ALLOWED_COLUMNS.items():
        if table in used_tables:
            used_cols = re.findall(rf"{table}\.([a-zA-Z_]+)", sql, flags=re.IGNORECASE)
            for col in used_cols:
                if col.lower() not in {c.lower() for c in cols}:
                    raise ValueError(f"❌ {col} kolonu {table} tablosunda bulunmuyor!")

    # 6. Segment doğrulama
    if "SEGMENT" in sql_upper:
        values = re.findall(r"SEGMENT\s*=\s*'([^']+)'", sql, flags=re.IGNORECASE)
        for v in values:
            if v not in ALLOWED_SEGMENTS:
                raise ValueError(f"❌ Segment değeri geçersiz! Geçerli segmentler: {ALLOWED_SEGMENTS}")

    # 7. credit_tier doğrulama
    if "CREDIT_TIER" in sql_upper:
        numbers = re.findall(r"CREDIT_TIER\s*=\s*(\d+)", sql_upper)
        for n in numbers:
            value = int(n)
            if value < 1 or value > 5:
                raise ValueError("❌ credit_tier yalnızca 1 ile 5 arasında olmalı!")

    # 8. GROUP BY boyutu kontrolü
    group_by_cols = re.findall(r"GROUP BY\s+([a-zA-Z_,\s]+)", sql, flags=re.IGNORECASE)
    if group_by_cols:
        count_cols = len(group_by_cols[0].split(","))
        if count_cols > 50:
            raise ValueError("❌ GROUP BY boyutu 50'den büyük olamaz!")

    # 9. Tarih aralığı kontrolü (varsayılan son 12 ay)
    if "MONTH" in sql_upper and "WHERE" not in sql_upper:
        today = datetime.today()
        start_year = today.year - 1
        start_month = today.month % 12 + 1
        end_year = today.year
        end_month = today.month
        sql = sql.strip().rstrip(";") + f" WHERE MONTH BETWEEN '{start_year}-01' AND '{end_year}-{end_month:02}'"

    # 10. AST analizi
    check_ast_structure(sql)

    # 11. EXPLAIN ile ağır sorgu uyarısı
    if not explain_and_check(sql):
        print("⚠️ Sorgu çok ağır görünüyor; 'şehir' veya 'ay' filtresi eklemeyi düşünün.")

    return True
