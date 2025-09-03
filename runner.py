import duckdb
import os
from guardrails import validate_sql, fix_segments
import time

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

            # Eğer log tablosu yoksa oluştur
            if "logs" not in existing_tables:
                self.conn.execute("""
                    CREATE TABLE logs (
                        ts TIMESTAMP,
                        user_question TEXT,
                        tables TEXT,
                        columns TEXT,
                        generated_sql TEXT,
                        guardrail_errors TEXT,
                        execution_time_ms INTEGER
                    )
                """)
                
    def execute_query(self, query: str):
        # Segmentleri düzelt
        query = fix_segments(query)

        # Guardrails ile SQL güvenlik kontrolü
        validate_sql(query)

        # Sadece SELECT’e izin ver
        if not query.strip().lower().startswith("select"):
            raise ValueError("❌ Sadece SELECT sorgularına izin veriliyor.")
        start = time.time()
        # Sorguyu çalıştır
        try:
            result_df = self.conn.execute(query).fetchdf()
            exec_time = int((time.time() - start) * 1000)  # ms cinsinden süre
            return result_df, exec_time
        except Exception as e:
            raise RuntimeError(f"❌ SQL çalıştırılamadı: {str(e)}")

    def log(self, user_question, tables, columns, sql, guardrail_errors, exec_time):
        """Bir sorgunun detaylarını logs tablosuna yazar"""
        self.conn.execute("""
            INSERT INTO logs (ts, user_question, tables, columns, generated_sql, guardrail_errors, execution_time_ms)
            VALUES (NOW(), ?, ?, ?, ?, ?, ?)
        """, [user_question, ",".join(tables), ",".join(columns), sql, guardrail_errors, exec_time])

    def close(self):
        """Bağlantıyı kapatır"""
        self.conn.close()
