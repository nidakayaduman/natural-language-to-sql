import duckdb
import pandas as pd
import os

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
                customers_df = pd.read_csv("data/customers.csv")
                self.conn.execute("CREATE TABLE customers AS SELECT * FROM customers_df")

            if "sales" not in existing_tables:
                sales_df = pd.read_csv("data/sales.csv")
                self.conn.execute("CREATE TABLE sales AS SELECT * FROM sales_df")

    def execute_query(self, query: str):
        """
        Güvenli SQL çalıştırma fonksiyonu.
        Guardrails sonrası gelen SQL'i alır, DataFrame döner.
        """
        # Yalnızca SELECT izinli
        if not query.strip().lower().startswith("select"):
            raise ValueError("❌ Sadece SELECT sorgularına izin veriliyor.")

        try:
            # Sorguyu çalıştır ve pandas DataFrame döndür
            result_df = self.conn.execute(query).fetchdf()
            return result_df
        except Exception as e:
            raise RuntimeError(f"❌ SQL çalıştırılamadı: {str(e)}")

    def close(self):
        """Bağlantıyı kapatır"""
        self.conn.close()
