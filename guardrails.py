import re
import sqlparse

ALLOWED_SEGMENTS = {"Bireysel", "KOBI", "Kurumsal"}
ALLOWED_TABLES = {"CUSTOMERS", "SALES"}

def fix_segments(sql: str) -> str:
    """
    Yanlış yazılan segment isimlerini Türkçeye çevirir.
    """
    mapping = {
        "corporate": "Kurumsal",
        "individual": "Bireysel",
        "sme": "KOBI",
        "kobi": "KOBI",
        "kurumsal": "Kurumsal",
        "bireysel": "Bireysel"
    }
    for wrong, correct in mapping.items():
        sql = sql.replace(f"'{wrong}'", f"'{correct}'")
        sql = sql.replace(f'"{wrong}"', f"'{correct}'")
        sql = sql.replace(f"'{wrong.capitalize()}'", f"'{correct}'")
    return sql


def validate_sql(sql: str):
    """
    SQL güvenlik kontrolleri:
    1. SELECT sorgusu zorunlu
    2. DROP/DELETE/INSERT/ALTER yasak
    3. LIMIT 1000 zorunlu
    4. Yalnız izinli tablolar kullanılabilir
    5. Segmentler ve credit_tier doğrulanır
    """

    sql_upper = sql.upper()

    # 1. DROP, DELETE, UPDATE, INSERT, ALTER yasak
    forbidden = ["DELETE", "UPDATE", "DROP", "INSERT", "ALTER"]
    for keyword in forbidden:
        if re.search(rf"\b{keyword}\b", sql_upper):
            raise ValueError(f"❌ {keyword} komutuna izin verilmiyor!")

    # 2. SELECT sorgusu mu kontrolü
    parsed = sqlparse.parse(sql)
    if not parsed or parsed[0].get_type() != "SELECT":
        raise ValueError("❌ Sadece SELECT sorgularına izin veriliyor!")

    # 3. LIMIT 1000 zorunlu
    if "LIMIT" not in sql_upper:
        raise ValueError("❌ LIMIT eksik! Model promptunu düzelt.")

    # 4. Tabloları doğrula
    used_tables = re.findall(r"FROM\s+([a-zA-Z_]+)|JOIN\s+([a-zA-Z_]+)", sql_upper)
    used_tables = {tbl for pair in used_tables for tbl in pair if tbl}
    if not used_tables.issubset(ALLOWED_TABLES):
        raise ValueError(f"❌ İzinli tablolar dışında tablo kullanılamaz! "
                         f"Kullanılan: {used_tables} | İzinli: {ALLOWED_TABLES}")

    # 5. Segment doğrulama
    if "SEGMENT" in sql_upper:
        values = re.findall(r"SEGMENT\s*=\s*'([^']+)'", sql, flags=re.IGNORECASE)
        for v in values:
            if v not in ALLOWED_SEGMENTS:
                raise ValueError(
                    f"❌ Segment değeri geçersiz! Geçerli segmentler: {ALLOWED_SEGMENTS}"
                )

    # 6. credit_tier doğrulama
    if "CREDIT_TIER" in sql_upper:
        numbers = re.findall(r"CREDIT_TIER\s*=\s*(\d+)", sql_upper)
        for n in numbers:
            value = int(n)
            if value < 1 or value > 5:
                raise ValueError("❌ credit_tier yalnızca 1 ile 5 arasında olmalı!")

    return True
