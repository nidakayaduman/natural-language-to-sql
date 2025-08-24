import duckdb
import os
from guardrails import validate_sql, fix_segments

class SQLRunner:
    def __init__(self, db_path: str = "data/database.duckdb", use_postgres=False, postgres_url=None):
        """
        SQLRunner sınıfı hem DuckDB hem PostgreSQL üzerinde sorgu çalıştırabilir.
        Default: DuckDB
        """
        self.use_postgres = use_postgres
        self.postgres_url = postgres_url

        if self.use_postgres:
            import psycopg2
            self.conn = psycopg2.connect(postgres_url)
        else:
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            self.conn = duckdb.connect(db_path)

            # Eğer tablo yoksa CSV'den otomatik yükle
            existing_tables = self.conn.execute("SHOW TABLES").fetchdf()["name"].tolist()

            if "customers" not in existing_tables:
                self.conn.execute("""
                    CREATE TABLE customers AS 
                    SELECT * FROM read_csv_auto('data/customers.csv', HEADER=TRUE)
                """)

            if "sales" not in existing_tables:
                self.conn.execute("""
                    CREATE TABLE sales AS 
                    SELECT * FROM read_csv_auto('data/sales.csv', HEADER=TRUE)
                """)

    def execute_query(self, query: str):
        # Segmentleri düzelt
        query = fix_segments(query)

        # Guardrails ile SQL güvenlik kontrolü
        validate_sql(query)

        # Sadece SELECT’e izin ver
        if not query.strip().lower().startswith("select"):
            raise ValueError("❌ Sadece SELECT sorgularına izin veriliyor.")

        # Sorguyu çalıştır
        try:
            result_df = self.conn.execute(query).fetchdf()
            return result_df
        except Exception as e:
            raise RuntimeError(f"❌ SQL çalıştırılamadı: {str(e)}")


    def close(self):
        """Bağlantıyı kapatır"""
        self.conn.close()
