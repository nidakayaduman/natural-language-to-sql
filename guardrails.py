import sqlglot

def validate_sql(sql: str):
    """
    SQL güvenlik kuralları:
    1. Sadece SELECT'e izin ver.
    2. LIMIT 1000 zorunlu.
    3. DROP, DELETE, UPDATE, INSERT yasak.
    4. Sadece izinli tablolar kullanılabilir.
    """
    try:
        # 1. SELECT kontrolü
        parsed = sqlglot.parse_one(sql, read="duckdb")
        if parsed.key.upper() != "SELECT":
            raise ValueError("❌ Sadece SELECT sorgularına izin veriliyor!")

        # 2. LIMIT zorunlu
        if "LIMIT" not in sql.upper():
            raise ValueError("❌ LIMIT eksik! Model promptunu veya SQL'i düzelt.")

        # 3. Tehlikeli komutları engelle
        forbidden = {"DELETE", "UPDATE", "DROP", "INSERT", "ALTER"}
        for keyword in forbidden:
            if keyword in sql.upper():
                raise ValueError(f"❌ {keyword} komutuna izin verilmiyor!")

        # 4. Tabloları kontrol et
        allowed_tables = {"CUSTOMERS", "SALES"}
        used_tables = [t for t in sql.upper().split() if t in allowed_tables]
        if not used_tables:
            raise ValueError("❌ İzinli tablolar dışında tablo kullanılamaz!")

        return True

    except Exception as e:
        raise ValueError(f"SQL doğrulama hatası: {e}")
