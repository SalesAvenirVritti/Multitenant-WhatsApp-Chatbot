import sys
import os

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db import Base
import app.models  # IMPORTANT: loads all models

# ==============================
# PostgreSQL (LOCAL - pgAdmin)
# ==============================
POSTGRES_URL = (
    "postgresql+psycopg2://postgres:Gorow%4023@localhost:5432/multitenant_chatbot"
)

# ==============================
# SQLite (OUTPUT FILE)
# ==============================
SQLITE_URL = "sqlite:///multitenant_chatbot.db"

# Create database engines
pg_engine = create_engine(POSTGRES_URL)
sqlite_engine = create_engine(
    SQLITE_URL,
    connect_args={"check_same_thread": False}
)

# Create tables in SQLite
Base.metadata.create_all(sqlite_engine)

# Create sessions
PGSession = sessionmaker(bind=pg_engine)
SQLiteSession = sessionmaker(bind=sqlite_engine)

pg = PGSession()
sqlite = SQLiteSession()

print("🚀 Starting PostgreSQL → SQLite migration...")

# Copy data table by table
for table in Base.metadata.sorted_tables:
    print(f"➡ Migrating table: {table.name}")

    result = pg.execute(table.select())
    rows = result.fetchall()

    if not rows:
        print(f"   ⚠ No data in {table.name}")
        continue

    columns = result.keys()
    data = []

    for row in rows:
        record = dict(zip(columns, row))

        # 🔧 FIX: handle NOT NULL constraint for tenants.domain_type
        if table.name == "tenants" and record.get("domain_type") is None:
            record["domain_type"] = "custom"  # default value

        data.append(record)

    sqlite.execute(table.insert(), data)
    print(f"   ✅ Inserted {len(data)} rows")

sqlite.commit()
pg.close()
sqlite.close()

print("\n🎉 MIGRATION COMPLETED SUCCESSFULLY")
print("📁 SQLite DB created: multitenant_chatbot.db")
