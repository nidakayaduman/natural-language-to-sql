import sqlglot

# İzin verilen segmentler ve tablolar
ALLOWED_SEGMENTS = {"Bireysel", "KOBI", "Kurumsal"}
ALLOWED_TABLES = {"CUSTOMERS", "SALES"}

def fix_segments(sql: str) -> str:
    """
    Yanlış yazılan segment isimlerini Türkçeye çevirir.
    Ör: 'individual' -> 'Bireysel'
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
    SQL güvenlik kuralları:
    1. Sadece SELECT sorgularına izin ver.
    2. LIMIT 1000 zorunlu.
    3. DROP, DELETE, UPDATE, INSERT, ALTER yasak.
    4. Sadece izinli tablolar kullanılabilir.
    5. Segment sadece 'Bireysel', 'KOBI', 'Kurumsal' olabilir.
    6. credit_tier sadece 1–5 arasında olmalı.
    """

    sql_upper = sql.upper()

    # 1. Tehlikeli komutları kontrol et
    forbidden = {"DELETE", "UPDATE", "DROP", "INSERT", "ALTER"}
    for keyword in forbidden:
        if keyword in sql_upper:
            raise ValueError(f"❌ {keyword} komutuna izin verilmiyor!")

    # 2. SQL'i parse et (DuckDB kullanıyoruz)
    try:
        parsed = sqlglot.parse_one(sql, read="duckdb")
    except Exception as e:
        raise ValueError(f"❌ SQL parse edilemedi: {str(e)}")

    # 3. Sadece SELECT sorgularına izin ver
    if not parsed or parsed.key.upper() != "SELECT":
        raise ValueError("❌ Sadece SELECT sorgularına izin veriliyor!")

    # 4. LIMIT 1000 zorunlu
    if "LIMIT" not in sql_upper:
        raise ValueError("❌ LIMIT eksik! Model promptunu veya SQL'i düzelt.")
    
    # 5. İzinli tablolar dışında tablo kullanımı yasak
    used_tables = {t.name.upper() for t in parsed.find_all("Table")}
    if not used_tables.issubset(ALLOWED_TABLES):
        raise ValueError(f"❌ İzinli tablolar dışında tablo kullanılamaz! "
                         f"Kullanılan: {used_tables} | İzinli: {ALLOWED_TABLES}")

    # 6. Segment doğrulama (YANLIŞ girilenleri yakala)
    for lit in parsed.find_all("Literal"):
        value = str(lit.this).strip("'\"")
        if "SEGMENT" in sql_upper and value not in ALLOWED_SEGMENTS:
                raise ValueError(
                    f"❌ Segment değeri geçersiz! Geçerli segmentler: {ALLOWED_SEGMENTS}"
                )


    # 7. credit_tier doğrulama (1 ile 5 arasında olmalı)
    if "CREDIT_TIER" in sql_upper:
        for lit in parsed.find_all("Literal"):
            if str(lit.this).isdigit():
                value = int(lit.this)
                if value < 1 or value > 5:
                    raise ValueError("❌ credit_tier yalnızca 1 ile 5 arasında olmalı!")

    return True
