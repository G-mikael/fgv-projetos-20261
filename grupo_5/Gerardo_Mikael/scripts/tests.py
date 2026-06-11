import sqlite3
import pandas as pd

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SQL_FILE_PATH = BASE_DIR.parent / "sql" / "mysqlsampledatabase.sql"

conn = sqlite3.connect(":memory:")

with open(SQL_FILE_PATH, "r", encoding="utf-8") as f:
    sql_script = f.read()

conn.executescript(sql_script)

customers = pd.read_sql("SELECT * FROM customers", conn)
employees = pd.read_sql("SELECT * FROM employees", conn)
offices = pd.read_sql("SELECT * FROM offices", conn)
orders = pd.read_sql("SELECT * FROM orders", conn)

