import os
from datetime import date

from dotenv import load_dotenv
from sqlmodel import Session, select

from database import create_db_and_tables, engine
from models import (Arcana, ChatKeyword, ImlekDate, Service, ShioAnimal, TarotCard,
                    User, ZodiacSign)
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

# Tanggal Imlek 1990-2030 (sudah dicek ulang dengan library kalender lunar).
IMLEK = {
    1990: "1990-01-27", 1991: "1991-02-15", 1992: "1992-02-04", 1993: "1993-01-23",
    1994: "1994-02-10", 1995: "1995-01-31", 1996: "1996-02-19", 1997: "1997-02-07",
    1998: "1998-01-28", 1999: "1999-02-16", 2000: "2000-02-05", 2001: "2001-01-24",
    2002: "2002-02-12", 2003: "2003-02-01", 2004: "2004-01-22", 2005: "2005-02-09",
    2006: "2006-01-29", 2007: "2007-02-18", 2008: "2008-02-07", 2009: "2009-01-26",
    2010: "2010-02-14", 2011: "2011-02-03", 2012: "2012-01-23", 2013: "2013-02-10",
    2014: "2014-01-31", 2015: "2015-02-19", 2016: "2016-02-08", 2017: "2017-01-28",
    2018: "2018-02-16", 2019: "2019-02-05", 2020: "2020-01-25", 2021: "2021-02-12",
    2022: "2022-02-01", 2023: "2023-01-22", 2024: "2024-02-10", 2025: "2025-01-29",
    2026: "2026-02-17", 2027: "2027-02-06", 2028: "2028-01-26", 2029: "2029-02-13",
    2030: "2030-02-03",
}

# ---------------------------------------------------------------- kamus chat (starter)
# Daftar awal buat demo. Kalibrasi pakai chat dummy dan cek ulang sitasi Gottman sebelum masuk laporan.
KEYWORDS = [
    ("criticism", "selalu,tidak pernah,kamu tuh,kenapa sih kamu,gak becus", "Gottman (Four Horsemen)", -2),
    ("contempt", "bodoh,males ah,terserah lu,dasar,sok tau", "Gottman (Four Horsemen)", -3),
    ("defensiveness", "bukan salah aku,kan kamu yang,aku udah bilang,lah kok aku", "Gottman (Four Horsemen)", -1),
    ("stonewalling", "terserah,ya udah,hmm,gapapa,capek ngomong", "Gottman (Four Horsemen)", -1),
    ("positive", "makasih,sayang,seneng,keren,bangga,mantap,kangen,hati-hati ya", "Rasio positif:negatif", 1),
    ("negative", "kesel,benci,males,bete,capek,kecewa", "Rasio positif:negatif", -1),
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

        for year, d in IMLEK.items():
            if not s.get(ImlekDate, year):
                s.add(ImlekDate(year=year, new_year_date=date.fromisoformat(d)))

        for cat, kws, src, w in KEYWORDS:
            if not s.exec(select(ChatKeyword).where(ChatKeyword.category == cat)).first():
                s.add(ChatKeyword(category=cat, keywords=kws, source=src, weight=w))

        s.commit()
    print("Seed selesai: admin, harga, 78 kartu tarot, 22 arcana, 12 zodiak, 12 shio, tanggal Imlek, kamus chat.")


if __name__ == "__main__":
    main()