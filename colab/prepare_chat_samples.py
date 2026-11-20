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
    r"(\d{1,2}:\d{2}(?::\d{2})?(?:\s?[APap][Mm])?)\]?\s*"
    r"(?:-\s*|\s+)([^:]{1,100}):\s?(.*)$"
)
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
URL_RE = re.compile(r"\b(?:https?://|www\.)\S+", re.I)
PHONE_RE = re.compile(r"(?<!\w)\+?\d[\d .()\-]{7,}\d(?!\w)")


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
            return datetime.strptime(f"{date_text} {time_text.upper()}", fmt)
        except ValueError:
            continue
    return None


def parse_export(text: str):
    lines = text.splitlines()
    month_first_evidence = day_first_evidence = 0
    for line in lines:
        match = LINE_RE.match(line.strip())
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
        match = LINE_RE.match(line.strip())
        if match:
            timestamp = parse_timestamp(match.group(1), match.group(2), month_first)
            if timestamp:
                messages.append([timestamp, match.group(3).strip(), match.group(4).strip()])
                continue
        if messages and line.strip():
            messages[-1][2] += "\n" + line.strip()
    return messages


def scrub_message(text: str, names: list[str]) -> str:
    for name in sorted((item for item in names if item), key=len, reverse=True):
        text = re.sub(rf"(?<!\w){re.escape(name)}(?!\w)", "[participant]", text, flags=re.I)
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
    archives = sorted(INPUT_DIR.glob("*.zip"))
    if not archives:
        raise SystemExit(f"No ZIP exports found in {INPUT_DIR}")

    rows = []
    conversations = Counter()
    for index, path in enumerate(archives, start=1):
        parsed = parse_export(read_zip(path))
        sender_counts = Counter(sender for _, sender, _ in parsed)
        participants = {sender: f"participant_{i}" for i, (sender, _) in enumerate(sender_counts.most_common(), start=1)}
        private_names = list(participants)
        conversation_id = f"conversation_{index:02d}"
        for timestamp, sender, body in parsed:
            rows.append({
                "conversation_id": conversation_id,
                "timestamp": timestamp.isoformat(sep=" "),
                "sender": participants[sender],
                "text": scrub_message(body, private_names),
            })
        conversations[conversation_id] = len(parsed)

    rows.sort(key=lambda row: (row["conversation_id"], row["timestamp"]))
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("conversation_id", "timestamp", "sender", "text"))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Created {OUTPUT_FILE.relative_to(ROOT)}")
    print(f"Conversations: {len(conversations)} | Parsed messages: {len(rows):,}")
    print("Participant labels, URLs, emails, and phone-number patterns were scrubbed.")
    print("Review message text for other identifying details before sharing or uploading it.")


if __name__ == "__main__":
    main()
