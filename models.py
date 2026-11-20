from datetime import date, datetime, timezone
from typing import Optional

from pydantic import NaiveDatetime
from sqlalchemy import Column, Text, UniqueConstraint
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


# =====================================================================
# USER & KEAMANAN
# =====================================================================
class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    email: str = Field(max_length=150, unique=True, index=True)
    password_hash: str = Field(max_length=255)
    role: str = Field(default="user", max_length=10)  # user / admin
    birth_date: Optional[date] = None
    avatar_url: Optional[str] = Field(default=None, max_length=300)
    is_active: bool = True
    failed_logins: int = 0
    locked_until: Optional[NaiveDatetime] = None
    totp_secret: Optional[str] = Field(default=None, max_length=64)  # 2FA (opsional)
    totp_enabled: bool = False
    created_at: NaiveDatetime = Field(default_factory=utcnow)


class LoginSession(SQLModel, table=True):
    """Sesi aktif per perangkat (layar Profile and Security > active sessions)."""
    __tablename__ = "login_sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    token_hash: str = Field(max_length=64, unique=True)  # simpan hash token, bukan token asli
    user_agent: str = Field(default="", max_length=200)
    ip: Optional[str] = Field(default=None, max_length=45)
    created_at: NaiveDatetime = Field(default_factory=utcnow)
    last_seen_at: NaiveDatetime = Field(default_factory=utcnow)
    revoked: bool = False


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    event: str = Field(max_length=40)
    detail: str = Field(default="", max_length=300)
    ip: Optional[str] = Field(default=None, max_length=45)
    created_at: NaiveDatetime = Field(default_factory=utcnow)


# =====================================================================
# MASTER DATA
# =====================================================================
class Service(SQLModel, table=True):
    """Master harga: chat / tarot / matrix / zodiac."""
    __tablename__ = "services"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(max_length=20, unique=True)
    name: str = Field(max_length=100)
    price: int = 0  # rupiah
    is_active: bool = True


class TarotCard(SQLModel, table=True):
    __tablename__ = "tarot_cards"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True)
    suit: str = Field(max_length=30)
    upright: str = Field(max_length=300)
    reversed_meaning: str = Field(max_length=300)
    image_url: Optional[str] = Field(default=None, max_length=300)


class Arcana(SQLModel, table=True):
    """22 Major Arcana untuk Destiny Matrix. Teks makna ditulis sendiri lewat Master Data."""
    __tablename__ = "arcana"

    id: Optional[int] = Field(default=None, primary_key=True)
    number: int = Field(unique=True)  # 1..22
    name: str = Field(max_length=60)
    keywords: str = Field(default="", max_length=200)
    personality: str = Field(default="", sa_column=Column(Text, nullable=False, server_default=""))
    talent: str = Field(default="", sa_column=Column(Text, nullable=False, server_default=""))
    life_purpose: str = Field(default="", sa_column=Column(Text, nullable=False, server_default=""))
    relationship: str = Field(default="", sa_column=Column(Text, nullable=False, server_default=""))
    career_money: str = Field(default="", sa_column=Column(Text, nullable=False, server_default=""))
    karmic_lesson: str = Field(default="", sa_column=Column(Text, nullable=False, server_default=""))


class ZodiacSign(SQLModel, table=True):
    __tablename__ = "zodiac_signs"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=30, unique=True)
    start_month: int
    start_day: int
    end_month: int
    end_day: int
    element: str = Field(max_length=20)
    traits: str = Field(default="", max_length=500)


class ShioAnimal(SQLModel, table=True):
    __tablename__ = "shio_animals"

    id: Optional[int] = Field(default=None, primary_key=True)
    cycle_index: int = Field(unique=True)  # 0 = Rat ... 11 = Pig
    name: str = Field(max_length=30, unique=True)
    traits: str = Field(default="", max_length=500)


class ImlekDate(SQLModel, table=True):
    """Tanggal Imlek per tahun. Shio berganti di tanggal ini, bukan 1 Januari."""
    __tablename__ = "imlek_dates"

    year: int = Field(primary_key=True)
    new_year_date: date


class ChatKeyword(SQLModel, table=True):
    """Kamus indikator chat (Gottman, positif/negatif, excited, dll)."""
    __tablename__ = "chat_keywords"

    id: Optional[int] = Field(default=None, primary_key=True)
    category: str = Field(max_length=30)
    keywords: str = Field(max_length=500)
    source: str = Field(default="", max_length=100)
    weight: int = 0
    is_active: bool = True


# =====================================================================
# TRANSAKSI
# =====================================================================
class Order(SQLModel, table=True):
    __tablename__ = "orders"

    id: Optional[int] = Field(default=None, primary_key=True)
    order_code: Optional[str] = Field(default=None, max_length=20, unique=True, index=True)  # ORD-xxxx
    user_id: int = Field(foreign_key="users.id", index=True)
    service_id: int = Field(foreign_key="services.id")
    amount: int  # snapshot harga saat order dibuat (diambil dari server, bukan dari browser)
    status: str = Field(default="pending", max_length=12)  # pending/paid/expired/failed/cancelled
    created_at: NaiveDatetime = Field(default_factory=utcnow)
    expires_at: Optional[NaiveDatetime] = None
    paid_at: Optional[NaiveDatetime] = None


class Payment(SQLModel, table=True):
    """Catatan pembayaran dari payment gateway (sandbox). Tidak boleh dihapus."""
    __tablename__ = "payments"

    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id", index=True)
    gateway: str = Field(default="midtrans", max_length=20)
    gateway_ref: Optional[str] = Field(default=None, max_length=100, unique=True)
    method: str = Field(default="", max_length=20)  # qris / va / ewallet
    amount: int
    status: str = Field(default="pending", max_length=12)  # pending/settlement/expire/deny/cancel
    signature_valid: bool = False
    created_at: NaiveDatetime = Field(default_factory=utcnow)
    settled_at: Optional[NaiveDatetime] = None


class WebhookEvent(SQLModel, table=True):
    """Biar notifikasi gateway idempotent: event yang sama tidak diproses dua kali."""
    __tablename__ = "webhook_events"

    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: str = Field(max_length=100, unique=True)
    order_code: Optional[str] = Field(default=None, max_length=20)
    status: str = Field(default="", max_length=20)
    received_at: NaiveDatetime = Field(default_factory=utcnow)


class Reading(SQLModel, table=True):
    """Header semua jenis reading (chat / tarot / matrix / zodiac). Dipakai My Readings dan Reports."""
    __tablename__ = "readings"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    type: str = Field(max_length=20)
    title: str = Field(max_length=150)
    order_id: Optional[int] = Field(default=None, foreign_key="orders.id")  # terisi kalau berbayar
    result_json: str = Field(default="", sa_column=Column(Text, nullable=False, server_default=""))
    created_at: NaiveDatetime = Field(default_factory=utcnow)


class TarotDraw(SQLModel, table=True):
    """Kartu yang keluar di satu reading tarot."""
    __tablename__ = "tarot_draws"
    __table_args__ = (UniqueConstraint("reading_id", "position"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    reading_id: int = Field(foreign_key="readings.id", index=True)
    card_id: int = Field(foreign_key="tarot_cards.id")
    position: int  # 1, 2, 3 ...
    position_label: str = Field(default="", max_length=30)  # Past / Present / Future
    is_reversed: bool = False


class MatrixReading(SQLModel, table=True):
    """Angka hasil hitung Destiny Matrix (tiap angka 1..22 merujuk ke arcana.number)."""
    __tablename__ = "matrix_readings"

    id: Optional[int] = Field(default=None, primary_key=True)
    reading_id: int = Field(foreign_key="readings.id", unique=True)
    birth_date: date
    day_num: int
    month_num: int
    year_num: int
    sum_num: int
    center_num: int


class ZodiacReading(SQLModel, table=True):
    __tablename__ = "zodiac_readings"

    id: Optional[int] = Field(default=None, primary_key=True)
    reading_id: int = Field(foreign_key="readings.id", unique=True)
    birth_date: date
    zodiac_id: int = Field(foreign_key="zodiac_signs.id")
    shio_id: int = Field(foreign_key="shio_animals.id")


class ChatSession(SQLModel, table=True):
    """Satu kali upload + analisis chat. Isi chat mentah TIDAK disimpan, hanya hasil hitungan."""
    __tablename__ = "chat_sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    reading_id: int = Field(foreign_key="readings.id", unique=True)
    source: str = Field(default="whatsapp", max_length=20)
    relationship_status: Optional[str] = Field(default=None, max_length=20)  # opsional
    my_gender: Optional[str] = Field(default=None, max_length=10)  # opsional
    other_gender: Optional[str] = Field(default=None, max_length=10)  # opsional
    my_alias: str = Field(default="You", max_length=50)  # nama sudah disamarkan
    other_alias: str = Field(default="Them", max_length=50)
    consent_given: bool = False  # centang persetujuan
    intent_enabled: bool = False  # centang analisis niat (kirim potongan ke AI)
    total_messages: int = 0
    first_message_at: Optional[NaiveDatetime] = None
    last_message_at: Optional[NaiveDatetime] = None
    status: str = Field(default="processing", max_length=12)  # processing/done/failed
    error_message: Optional[str] = Field(default=None, max_length=200)
    interest_trend: Optional[str] = Field(default=None, max_length=10)  # falling/steady/rising
    created_at: NaiveDatetime = Field(default_factory=utcnow)


class ChatPersonStat(SQLModel, table=True):
    """Statistik per orang (2 baris per sesi: me / other)."""
    __tablename__ = "chat_person_stats"
    __table_args__ = (UniqueConstraint("chat_session_id", "person"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    chat_session_id: int = Field(foreign_key="chat_sessions.id", index=True)
    person: str = Field(max_length=5)  # me / other
    bubbles: int = 0
    avg_length: float = 0
    reply_rate: float = 0  # 0..1
    first_message_pct: float = 0  # 0..1
    median_response_sec: Optional[int] = None  # jeda jam tidur tidak dihitung
    double_texts: int = 0
    question_count: int = 0
    deleted_count: int = 0
    excited_score: int = 0  # 0..100
    excited_factors: str = Field(default="", max_length=500)  # JSON: tanda seru, emoji, dst
    hourly_json: str = Field(default="", max_length=600)  # pesan per jam (24 angka)


class ChatIndicatorScore(SQLModel, table=True):
    """Hasil hitung indikator per kategori kamus (Gottman, positif/negatif)."""
    __tablename__ = "chat_indicator_scores"

    id: Optional[int] = Field(default=None, primary_key=True)
    chat_session_id: int = Field(foreign_key="chat_sessions.id", index=True)
    person: str = Field(max_length=5)
    category: str = Field(max_length=30)
    hit_count: int = 0


class ChatSignal(SQLModel, table=True):
    """Sinyal niat (opsional, AI): ada kutipan dan tingkat keyakinan, bukan vonis."""
    __tablename__ = "chat_signals"

    id: Optional[int] = Field(default=None, primary_key=True)
    chat_session_id: int = Field(foreign_key="chat_sessions.id", index=True)
    signal: str = Field(max_length=100)
    quote: str = Field(default="", max_length=300)
    confidence: str = Field(default="low", max_length=10)  # low / medium / high
