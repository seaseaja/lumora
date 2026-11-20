"""Convert local WhatsApp ZIP exports into an anonymized analysis CSV.

The exported CSV contains message text, so keep it local and do not publish it.
The source ZIP files are expected in ../sampel-chat/ and are ignored by Git.
"""

import csv
import re
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = ROOT / "sampel-chat"
OUTPUT_FILE = Path(__file__).resolve().parent / "sample_chat_messages.csv"
LINE_RE = re.compile(
    r"^\[?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}),?\s+"
    r"(\d{1,2}[:.]\d{2}(?:[:.]\d{2})?(?:\s?[APap][Mm])?)\]?\s*"
    r"(?:-\s*|\s+)([^:]{1,100}):\s?(.*)$"
)
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
URL_RE = re.compile(r"\b(?:https?://|www\.)\S+", re.I)
PHONE_RE = re.compile(r"(?<!\w)\+?\d[\d .()\-]{7,}\d(?!\w)")
MEDIA_RE = re.compile(
    r"^<?\s*(?:media omitted|.*omitted|.*tidak disertakan|.*dihapus|this message was deleted|pesan ini telah dihapus)\s*>?$",
    re.I,
)
SAMPLE_NO_RE = re.compile(r"(\d+)")


def decode_export(payload: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-16"):
        try:
            return payload.decode(encoding)
        except UnicodeDecodeError:
            pass
    raise ValueError("A chat export is not UTF-8 or UTF-16 text.")


def parse_timestamp(date_text: str, time_text: str, month_first: bool):
    date_orders = ("%m/%d", "%d/%m") if month_first else ("%d/%m", "%m/%d")
    formats = [
        f"{order}/{year} {clock}"
        for order in date_orders
        for year in ("%y", "%Y")
        for clock in ("%H:%M:%S", "%H:%M", "%I:%M:%S %p", "%I:%M %p")
    ]
    for fmt in formats:
        try:
            return datetime.strptime(f"{date_text} {time_text.replace('.', ':').upper()}", fmt)
        except ValueError:
            continue
    return None


def parse_export(text: str):
    lines = text.splitlines()
    month_first_evidence = day_first_evidence = 0
    for line in lines:
        match = LINE_RE.match(line.lstrip("\u200e\u200f\ufeff").rstrip())
        if not match:
            continue
        first, second = (int(part) for part in re.split(r"[/-]", match.group(1))[:2])
        if first <= 12 < second:
            month_first_evidence += 1
        elif second <= 12 < first:
            day_first_evidence += 1
    month_first = month_first_evidence > day_first_evidence

    messages = []
    for line in lines:
        match = LINE_RE.match(line.lstrip("\u200e\u200f\ufeff").rstrip())
        if match:
            timestamp = parse_timestamp(match.group(1), match.group(2), month_first)
            if timestamp:
                messages.append([timestamp, match.group(3).strip(), match.group(4).strip()])
                continue
        if messages and line.strip():
            messages[-1][2] += "\n" + line.strip()
    return messages


def name_patterns(names: list[str]):
    """Full sender names plus each word of 3+ letters; the last letter may repeat (e.g. "Chelseaaa")."""
    parts = set()
    for name in names:
        if name:
            parts.add(name)
            parts.update(word for word in re.findall(r"[^\W\d_]{3,}", name))
    return [
        re.compile(rf"(?<!\w){re.escape(part[:-1])}{re.escape(part[-1])}+(?!\w)", re.I)
        for part in sorted(parts, key=len, reverse=True)
    ]


def scrub_message(text: str, names: list[str]) -> str:
    for pattern in name_patterns(names):
        text = pattern.sub("[participant]", text)
    text = URL_RE.sub("[URL]", text)
    text = EMAIL_RE.sub("[EMAIL]", text)
    text = PHONE_RE.sub("[PHONE]", text)
    return text.strip()


def read_zip(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        entries = [
            item for item in archive.infolist()
            if not item.is_dir()
            and item.filename.lower().endswith(".txt")
            and not item.filename.startswith("__MACOSX/")
        ]
        if len(entries) != 1:
            raise ValueError(f"{path.name}: expected exactly one WhatsApp .txt export")
        if entries[0].file_size > 25 * 1024 * 1024:
            raise ValueError(f"{path.name}: uncompressed export exceeds 25 MB")
        return decode_export(archive.read(entries[0]))


def main():
    # Natural sort so "sampel 2" comes before "sampel 10"; the ID reuses the sample number.
    def sample_number(path: Path) -> int:
        match = SAMPLE_NO_RE.search(path.stem)
        return int(match.group(1)) if match else 10_000
    archives = sorted(INPUT_DIR.glob("*.zip"), key=lambda path: (sample_number(path), path.name))
    if not archives:
        raise SystemExit(f"No ZIP exports found in {INPUT_DIR}")

    rows = []
    conversations = Counter()
    for index, path in enumerate(archives, start=1):
        parsed = parse_export(read_zip(path))
        sender_counts = Counter(sender for _, sender, _ in parsed)
        participants = {sender: f"participant_{i}" for i, (sender, _) in enumerate(sender_counts.most_common(), start=1)}
        private_names = list(participants)
        number = sample_number(path)
        conversation_id = f"conversation_{number if number < 10_000 else index:02d}"
        if not parsed:
            print(f"WARNING: {path.name} produced no messages; check its date/time format.")
        for timestamp, sender, body in parsed:
            rows.append({
                "conversation_id": conversation_id,
                "timestamp": timestamp.isoformat(sep=" "),
                "sender": participants[sender],
                "text": scrub_message(body, private_names),
                "is_media": int(bool(MEDIA_RE.match(body.strip()))),
            })
        conversations[conversation_id] = len(parsed)

    rows.sort(key=lambda row: (row["conversation_id"], row["timestamp"]))
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("conversation_id", "timestamp", "sender", "text", "is_media"))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Created {OUTPUT_FILE.relative_to(ROOT)}")
    print(f"Conversations: {len(conversations)} | Parsed messages: {len(rows):,}")
    print("Participant labels, URLs, emails, and phone-number patterns were scrubbed.")
    print("Review message text for other identifying details before sharing or uploading it.")


if __name__ == "__main__":
    main()
