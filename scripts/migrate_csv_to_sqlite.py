import pandas as pd
import sqlite3
from pathlib import Path

CSV_PATH = "data/habits.csv"
DB_PATH = "db/habits.db"

# Load CSV
df = pd.read_csv(CSV_PATH)
df["date"] = pd.to_datetime(df["date"]).astype(str)

# Ensure db folder exists
Path("db").mkdir(exist_ok=True)

# Connect to SQLite
conn = sqlite3.connect(DB_PATH)

# Write to database
df.to_sql("habits", conn, if_exists="replace", index=False)

conn.close()

print("✅ Migration completed: CSV → SQLite")