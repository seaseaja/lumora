"""Import a licensed tarot deck from static/tarot_cards into the Tarot master data.

Name files after their card, for example: the_fool.jpg, ace_of_wands.webp.
Run: python import_tarot_art.py
"""
import re
from pathlib import Path

from sqlmodel import Session, select

from database import engine
from models import TarotCard

BASE_DIR = Path(__file__).resolve().parent
ART_DIR = BASE_DIR / "static" / "tarot_cards"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def normalized_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")


def valid_image(path: Path) -> bool:
    data = path.read_bytes()[:12]
    return (
        data.startswith(b"\x89PNG\r\n\x1a\n")
        or data.startswith(b"\xff\xd8\xff")
        or (len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP")
    )


def main():
    ART_DIR.mkdir(parents=True, exist_ok=True)
    files = [p for p in ART_DIR.iterdir() if p.is_file() and p.suffix.casefold() in IMAGE_EXTENSIONS]
    by_name = {normalized_name(path.stem): path for path in files if valid_image(path)}
    updated = 0
    missing = []
    with Session(engine) as session:
        cards = session.exec(select(TarotCard).order_by(TarotCard.name)).all()
        for card in cards:
            image = by_name.get(normalized_name(card.name))
            if not image:
                missing.append(card.name)
                continue
            card.image_url = f"/static/tarot_cards/{image.name}"
            session.add(card)
            updated += 1
        session.commit()
    print(f"Imported or updated artwork for {updated} card(s).")
    if missing:
        print(f"No matching image for {len(missing)} card(s):")
        for name in missing:
            print(f"- {name}")
    print("Add missing images to static/tarot_cards and run this script again.")


if __name__ == "__main__":
    main()
