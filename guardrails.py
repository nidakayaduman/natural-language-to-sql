import sqlglot

ALLOWED_SEGMENTS = {"Bireysel", "KOBI", "Kurumsal"}
ALLOWED_TABLES = {"CUSTOMERS", "SALES"}

def fix_segments(sql: str) -> str:
    """Yanlış segment isimlerini Türkçeye çevirir"""
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
    SQL güvenlik kuralları:
    1. Sadece SELECT sorgularına izin ver.
    2. LIMIT 1000 zorunlu.
    3. DROP, DELETE, UPDATE, INSERT yasak.
    4. Sadece izinli tablolar kullanılabilir.
    5. segment sadece 'Bireysel', 'KOBI', 'Kurumsal' olabilir.
    6. credit_tier sadece 1–5 arasında olmalı.
    """
    sql_upper = sql.upper()

    # 1. Tehlikeli komutları parse etmeden engelle
    forbidden = {"DELETE", "UPDATE", "DROP", "INSERT", "ALTER"}
    for keyword in forbidden:
        if keyword in sql_upper:
            raise ValueError(f"❌ {keyword} komutuna izin verilmiyor!")

    # 2. SELECT kontrolü
    parsed = sqlglot.parse_one(sql, read="duckdb")
    if parsed.key.upper() != "SELECT":
        raise ValueError("❌ Sadece SELECT sorgularına izin veriliyor!")

    # 3. LIMIT zorunlu
    if "LIMIT" not in sql_upper:
        raise ValueError("❌ LIMIT eksik! Model promptunu veya SQL'i düzelt.")

    # 4. İzinli tablo kontrolü
    used_tables = {t.name.upper() for t in parsed.find_all("Table")}
    if not used_tables.issubset(ALLOWED_TABLES):
        raise ValueError("❌ İzinli tablolar dışında tablo kullanılamaz!")

    # 5. Segment doğrulama
    for seg in parsed.find_all("Literal"):
        if seg.this in ["Bireysel", "KOBI", "Kurumsal"]:
            continue
        if "SEGMENT" in sql_upper and seg.is_string and seg.this not in ALLOWED_SEGMENTS:
            raise ValueError("❌ Segment sadece 'Bireysel', 'KOBI' veya 'Kurumsal' olabilir!")

    # 6. credit_tier doğrulama
    if "CREDIT_TIER" in sql_upper:
        for lit in parsed.find_all("Literal"):
        # Sadece sayısal değerleri kontrol et
            try:
                value = int(lit.this)
                if value < 1 or value > 5:
                    raise ValueError("❌ credit_tier yalnızca 1 ile 5 arasında olmalı!")
            except (ValueError, TypeError):
                # Sayı değilse atla
                continue


    return True
