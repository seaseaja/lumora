"""
Update database lama (Tahap 1) ke skema baru tanpa menghapus data.
create_all hanya bikin tabel BARU, jadi kolom baru di tabel lama ditambah lewat ALTER di sini.
Aman dijalankan berkali-kali:  python migrate.py
"""
from sqlalchemy import text

from database import create_db_and_tables, engine
import models  # noqa: F401  (supaya semua tabel terdaftar)

ALTERS = [
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS totp_secret VARCHAR(64)",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS totp_enabled BOOLEAN NOT NULL DEFAULT FALSE",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(300)",
    "ALTER TABLE tarot_cards ADD COLUMN IF NOT EXISTS image_url VARCHAR(300)",
    "ALTER TABLE orders ADD COLUMN IF NOT EXISTS order_code VARCHAR(20)",
    "ALTER TABLE orders ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP",
    "ALTER TABLE chat_keywords ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE",
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_orders_order_code ON orders (order_code)",
]

create_db_and_tables()  # bikin tabel-tabel baru dulu (database kosong seperti Neon baru)

with engine.begin() as conn:
    for stmt in ALTERS:
        conn.execute(text(stmt))
print("Migrasi selesai.")
