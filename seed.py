import os

from dotenv import load_dotenv
from sqlmodel import Session, select

from database import create_db_and_tables, engine
from lunar_new_year import IMLEK_DATES
from models import (Arcana, ChatKeyword, ImlekDate, Service, ShioAnimal, TarotCard,
                    User, ZodiacSign)
from patterns import DEFAULT_KEYWORDS, PREVIOUS_DEFAULTS
from security import hash_password

load_dotenv()

# ---------------------------------------------------------------- services
SERVICES = [
    ("chat", "Chat Analysis", 0),
    ("tarot", "Tarot full reading", 10000),
    ("matrix", "Destiny Matrix full reading", 10000),
    ("zodiac", "Zodiac and Shio", 0),
]

# ---------------------------------------------------------------- tarot (78 kartu)
# Makna di bawah cuma STARTER biar fitur bisa jalan. Tulis ulang dengan kata-katamu sendiri
# lewat halaman Master Data > Tarot Cards (jangan copy-paste dari situs lain).
MAJORS = [
    ("The Fool", "New beginnings, trust, a leap of faith", "Recklessness, hesitation"),
    ("The Magician", "Willpower, skill, using what you have", "Manipulation, untapped talent"),
    ("The High Priestess", "Intuition, quiet knowledge", "Ignoring your gut, secrets"),
    ("The Empress", "Nurturing, abundance, creativity", "Smothering, creative block"),
    ("The Emperor", "Structure, authority, stability", "Rigidity, control issues"),
    ("The Hierophant", "Tradition, guidance, shared values", "Rebellion, breaking convention"),
    ("The Lovers", "Connection, alignment, a meaningful choice", "Disharmony, misaligned values"),
    ("The Chariot", "Drive, determination, victory", "Lack of direction, scattered effort"),
    ("Strength", "Courage, patience, gentle control", "Self-doubt, low energy"),
    ("The Hermit", "Reflection, solitude, inner guidance", "Isolation, withdrawing too far"),
    ("Wheel of Fortune", "Change, luck, a turning point", "Resisting change, bad timing"),
    ("Justice", "Fairness, truth, accountability", "Unfairness, avoiding responsibility"),
    ("The Hanged Man", "Pause, new perspective, letting go", "Stalling, pointless sacrifice"),
    ("Death", "Endings, transformation, closure", "Clinging to the past, slow change"),
    ("Temperance", "Balance, moderation, patience", "Excess, imbalance"),
    ("The Devil", "Attachment, temptation, feeling stuck", "Breaking free, reclaiming control"),
    ("The Tower", "Sudden change, upheaval, a reveal", "Avoiding disaster, delayed change"),
    ("The Star", "Hope, renewal, calm", "Discouragement, lost faith"),
    ("The Moon", "Uncertainty, illusion, subconscious", "Clarity returning, release of fear"),
    ("The Sun", "Joy, success, vitality", "Temporary gloom, dimmed optimism"),
    ("Judgement", "Reckoning, renewal, a clear call", "Self-doubt, ignoring the call"),
    ("The World", "Completion, wholeness, achievement", "Loose ends, almost there"),
]
SUITS = {
    "Wands": "energy and action",
    "Cups": "feelings and relationships",
    "Swords": "thoughts and communication",
    "Pentacles": "work and money",
}
RANKS = [
    ("Ace", "a fresh start"), ("Two", "balance and choice"), ("Three", "growth and teamwork"),
    ("Four", "stability and rest"), ("Five", "conflict and loss"), ("Six", "harmony and progress"),
    ("Seven", "reflection and patience"), ("Eight", "movement and focus"),
    ("Nine", "resilience, nearly there"), ("Ten", "culmination and weight"),
    ("Page", "curiosity and new messages"), ("Knight", "pursuit and momentum"),
    ("Queen", "mature care and skill"), ("King", "authority and mastery"),
]


def build_cards():
    cards = [(n, "Major Arcana", u, r) for n, u, r in MAJORS]
    for suit, theme in SUITS.items():
        for rank, kw in RANKS:
            cards.append((f"{rank} of {suit}", suit, f"{kw.capitalize()} in {theme}",
                          f"Blocked or delayed: {kw} in {theme}"))
    return cards


# ---------------------------------------------------------------- arcana (matrix 1..22)
ARCANA = [
    (1, "The Magician", "Initiative, skill, manifestation"),
    (2, "The High Priestess", "Intuition, depth, inner knowing"),
    (3, "The Empress", "Creativity, care, abundance"),
    (4, "The Emperor", "Structure, leadership, discipline"),
    (5, "The Hierophant", "Teaching, tradition, values"),
    (6, "The Lovers", "Choice, connection, harmony"),
    (7, "The Chariot", "Drive, direction, victory"),
    (8, "Justice", "Fairness, balance, cause and effect"),
    (9, "The Hermit", "Reflection, wisdom, solitude"),
    (10, "Wheel of Fortune", "Cycles, change, luck"),
    (11, "Strength", "Courage, patience, inner power"),
    (12, "The Hanged Man", "Surrender, new perspective, pause"),
    (13, "Death", "Endings, transformation, release"),
    (14, "Temperance", "Moderation, healing, blending"),
    (15, "The Devil", "Attachment, temptation, shadow"),
    (16, "The Tower", "Upheaval, truth, rebuilding"),
    (17, "The Star", "Hope, inspiration, renewal"),
    (18, "The Moon", "Intuition, illusion, subconscious"),
    (19, "The Sun", "Joy, clarity, vitality"),
    (20, "Judgement", "Awakening, calling, reckoning"),
    (21, "The World", "Completion, integration, success"),
    (22, "The Fool", "Freedom, beginnings, trust"),
]

# ---------------------------------------------------------------- zodiak
ZODIACS = [
    ("Capricorn", 12, 22, 1, 19, "Earth", "Disciplined, ambitious, practical"),
    ("Aquarius", 1, 20, 2, 18, "Air", "Independent, inventive, detached"),
    ("Pisces", 2, 19, 3, 20, "Water", "Empathetic, dreamy, artistic"),
    ("Aries", 3, 21, 4, 19, "Fire", "Bold, energetic, impatient"),
    ("Taurus", 4, 20, 5, 20, "Earth", "Steady, loyal, stubborn"),
    ("Gemini", 5, 21, 6, 20, "Air", "Curious, talkative, adaptable"),
    ("Cancer", 6, 21, 7, 22, "Water", "Caring, protective, moody"),
    ("Leo", 7, 23, 8, 22, "Fire", "Confident, generous, attention-loving"),
    ("Virgo", 8, 23, 9, 22, "Earth", "Analytical, careful, perfectionist"),
    ("Libra", 9, 23, 10, 22, "Air", "Fair, social, indecisive"),
    ("Scorpio", 10, 23, 11, 21, "Water", "Intense, private, determined"),
    ("Sagittarius", 11, 22, 12, 21, "Fire", "Adventurous, honest, restless"),
]

# ---------------------------------------------------------------- shio (urutan siklus, 0 = Tikus)
SHIOS = [
    (0, "Rat", "Quick-witted, resourceful"), (1, "Ox", "Reliable, hardworking"),
    (2, "Tiger", "Brave, competitive"), (3, "Rabbit", "Gentle, diplomatic"),
    (4, "Dragon", "Confident, charismatic"), (5, "Snake", "Wise, reserved"),
    (6, "Horse", "Free-spirited, energetic"), (7, "Goat", "Creative, easygoing"),
    (8, "Monkey", "Clever, playful"), (9, "Rooster", "Organized, outspoken"),
    (10, "Dog", "Loyal, honest"), (11, "Pig", "Generous, sociable"),
]

# Tanggal Imlek 1900-2050 ada di lunar_new_year.py supaya app dan seed memakai tabel yang sama.

# ---------------------------------------------------------------- kamus chat
# Kamus pola komunikasi (Gottman) ada di patterns.py supaya app dan seed memakai daftar yang sama.
KEYWORDS = [(cat, kws, src, w) for cat, (kws, src, w) in DEFAULT_KEYWORDS.items()] + [
    ("excited", "wkwk,haha,yeay,wah,asik,gas,seru", "Heuristik excited", 1),
]


def main():
    create_db_and_tables()
    email, pw = os.getenv("ADMIN_EMAIL"), os.getenv("ADMIN_PASSWORD")
    if not email or not pw:
        raise SystemExit("Isi ADMIN_EMAIL dan ADMIN_PASSWORD di file .env dulu")
    with Session(engine) as s:
        if not s.exec(select(User).where(User.email == email.lower())).first():
            s.add(User(name="Admin", email=email.lower(), password_hash=hash_password(pw), role="admin"))

        for code, name, price in SERVICES:
            if not s.exec(select(Service).where(Service.code == code)).first():
                s.add(Service(code=code, name=name, price=price))

        for name, suit, up, rev in build_cards():
            if not s.exec(select(TarotCard).where(TarotCard.name == name)).first():
                s.add(TarotCard(name=name, suit=suit, upright=up, reversed_meaning=rev))

        for num, name, kw in ARCANA:
            if not s.exec(select(Arcana).where(Arcana.number == num)).first():
                s.add(Arcana(number=num, name=name, keywords=kw))

        for name, sm, sd, em, ed, el, tr in ZODIACS:
            if not s.exec(select(ZodiacSign).where(ZodiacSign.name == name)).first():
                s.add(ZodiacSign(name=name, start_month=sm, start_day=sd, end_month=em,
                                 end_day=ed, element=el, traits=tr))

        for idx, name, tr in SHIOS:
            if not s.exec(select(ShioAnimal).where(ShioAnimal.cycle_index == idx)).first():
                s.add(ShioAnimal(cycle_index=idx, name=name, traits=tr))

        for year, d in IMLEK_DATES.items():
            if not s.get(ImlekDate, year):
                s.add(ImlekDate(year=year, new_year_date=d))

        for cat, kws, src, w in KEYWORDS:
            row = s.exec(select(ChatKeyword).where(ChatKeyword.category == cat)).first()
            if not row:
                s.add(ChatKeyword(category=cat, keywords=kws, source=src, weight=w))
            elif row.keywords == PREVIOUS_DEFAULTS.get(cat):
                # Upgrade the untouched first-version list; edited lists are left as they are.
                row.keywords = kws
                s.add(row)

        s.commit()
    print("Seed selesai: admin, harga, 78 kartu tarot, 22 arcana, 12 zodiak, 12 shio, tanggal Imlek, kamus chat.")


if __name__ == "__main__":
    main()