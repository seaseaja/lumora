"""Rule-based closeness level for a two-person WhatsApp chat.

No trained model is involved: six communication signals are scored 0..1,
weighted, and summed into a 0-100 score. Every threshold below is a heuristic
chosen for this project. Use colab/validate_closeness.py to compare the
scores with human labels before tuning them.

`messages` everywhere is a list of (datetime, sender, body) sorted by time,
already filtered to the two participants in `people`.
"""

import calendar
import re
from collections import Counter, defaultdict

SESSION_GAP_SEC = 6 * 60 * 60  # same rule as the report: a 6-hour gap starts a new conversation
MEDIA_PATTERN = re.compile(r"omitted|tidak disertakan|was deleted|telah dihapus", re.I)
# Whole-word patterns so "sadar" or "tolol" do not match short terms by accident.
WARM_PATTERN = re.compile(
    r"\b(?:makasih|terima kasih|thanks|thank you|thx|sayang|kangen|rindu|miss you|love you|"
    r"hati-hati|hati hati|semangat|peluk|hug|bangga|proud|seneng|senang|happy|"
    r"w+k+w+[wk]*|(?:ha){2,}h?|(?:he){2,}h?)\b|❤|♥|🥰|😘|🤗|😍|💕|💖",
    re.I,
)
CLOSENESS_LEVELS = (  # (minimum score, label, description), highest first
    (75, "Very close", "Frequent, balanced, and quick back-and-forth with regular warm wording."),
    (55, "Close", "Regular contact where both people take part and reply fairly quickly."),
    (35, "Casual", "Contact happens, but less often or with one person carrying more of it."),
    (0, "Distant", "Occasional or one-sided contact with slow replies."),
)
LEVEL_NAMES = [level[1] for level in reversed(CLOSENESS_LEVELS)]  # Distant .. Very close

MIN_MESSAGES_PER_MONTH = 20  # fewer than this and a monthly score is mostly noise
TREND_THRESHOLD = 8  # points of change between early and recent months that count as a trend


def _scale(value: float, low: float, high: float) -> float:
    """Map value linearly onto 0..1 between low and high (clamped)."""
    if high == low:
        return 0.0
    return max(0.0, min(1.0, (value - low) / (high - low)))


def level_for(score: int) -> tuple[str, str]:
    """Return (label, description) for a 0-100 score."""
    _, label, description = next(level for level in CLOSENESS_LEVELS if score >= level[0])
    return label, description


def _openers_and_replies(messages, people):
    """Who starts each conversation, and each person's median reply time in seconds."""
    openers = Counter()
    responses = {person: [] for person in people}
    previous = None
    for timestamp, sender, _ in messages:
        gap = None if previous is None else (timestamp - previous[0]).total_seconds()
        if gap is None or gap >= SESSION_GAP_SEC:
            openers[sender] += 1
        elif sender != previous[1]:
            responses[sender].append(gap)
        previous = (timestamp, sender)
    medians = {}
    for person, values in responses.items():
        values.sort()
        medians[person] = values[len(values) // 2] if values else None
    return openers, medians


def compute_closeness(messages, people, span_days: int | None = None):
    """Score how closely two people communicate in `messages`.

    span_days is the number of calendar days the messages are judged against
    for consistency; by default the first to the last message.
    """
    if span_days is None:
        span_days = (messages[-1][0].date() - messages[0][0].date()).days + 1
    active_days = len({timestamp.date() for timestamp, _, _ in messages})
    per_active_day = len(messages) / max(active_days, 1)

    sender_counts = Counter(sender for _, sender, _ in messages)
    smaller_share = min(sender_counts[person] for person in people) / max(len(messages), 1)

    openers, medians = _openers_and_replies(messages, people)
    replies = [medians[person] for person in people if medians[person] is not None]
    median_reply = sum(replies) / len(replies) if replies else None
    total_openers = sum(openers[person] for person in people)
    opener_share = (min(openers[person] for person in people) / total_openers) if total_openers else 0.5

    text_messages = [body for _, _, body in messages if not MEDIA_PATTERN.search(body)]
    warm_rate = sum(1 for body in text_messages if WARM_PATTERN.search(body)) / max(len(text_messages), 1)

    if median_reply is None:
        reply_detail = "Not enough replies"
    elif median_reply >= 60:
        reply_detail = f"Typical reply in {median_reply / 60:.0f} min"
    else:
        reply_detail = f"Typical reply in {median_reply:.0f} sec"

    components = [
        {"key": "frequency", "label": "Chat frequency", "weight": 25,
         "value": _scale(per_active_day, 5, 60),
         "detail": f"{per_active_day:.0f} messages per active day"},
        {"key": "consistency", "label": "Consistency", "weight": 15,
         "value": _scale(active_days / max(span_days, 1), 0.05, 0.7),
         "detail": f"Talked on {active_days} of {span_days} days"},
        {"key": "balance", "label": "Message balance", "weight": 20,
         "value": _scale(smaller_share, 0.15, 0.45),
         "detail": f"Quieter person sent {smaller_share * 100:.0f}% of messages"},
        # 2 minutes or faster scores full marks; 3 hours or slower scores zero.
        {"key": "reply", "label": "Reply speed", "weight": 20,
         "value": 0.0 if median_reply is None else 1 - _scale(median_reply, 120, 3 * 60 * 60),
         "detail": reply_detail},
        {"key": "initiative", "label": "Who starts chats", "weight": 10,
         "value": _scale(opener_share, 0.1, 0.4),
         "detail": f"Less frequent starter opened {opener_share * 100:.0f}% of conversations"},
        {"key": "warmth", "label": "Warm wording", "weight": 10,
         "value": _scale(warm_rate, 0.02, 0.15),
         "detail": f"{warm_rate * 100:.0f}% of text messages"},
    ]
    score = round(sum(item["value"] * item["weight"] for item in components))
    for item in components:
        item["points"] = round(item["value"] * item["weight"], 1)
        item["value"] = round(item["value"], 3)
    label, description = level_for(score)
    return {"score": score, "level": label, "description": description,
            "levels": [{"min": level[0], "label": level[1]} for level in CLOSENESS_LEVELS],
            "components": components}


def closeness_by_month(messages, people):
    """Score each calendar month separately and describe the overall direction.

    A month with fewer than MIN_MESSAGES_PER_MONTH messages, or where only one
    person wrote, is listed with score None instead of a misleading number.
    Consistency is judged against the days of that month the export covers, so a
    partial first or last month is not penalised for days before or after the export.
    """
    first_day, last_day = messages[0][0].date(), messages[-1][0].date()
    by_month = defaultdict(list)
    for message in messages:
        by_month[(message[0].year, message[0].month)].append(message)

    months = []
    year, month = first_day.year, first_day.month
    while (year, month) <= (last_day.year, last_day.month):
        rows = by_month.get((year, month), [])
        days_in_month = calendar.monthrange(year, month)[1]
        start = first_day.day if (year, month) == (first_day.year, first_day.month) else 1
        end = last_day.day if (year, month) == (last_day.year, last_day.month) else days_in_month
        entry = {"month": f"{year}-{month:02d}", "label": f"{calendar.month_abbr[month]} {year % 100:02d}",
                 "messages": len(rows), "score": None, "level": None}
        if len(rows) >= MIN_MESSAGES_PER_MONTH and len({sender for _, sender, _ in rows}) == 2:
            result = compute_closeness(rows, people, span_days=end - start + 1)
            entry["score"], entry["level"] = result["score"], result["level"]
        months.append(entry)
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)

    scored = [entry["score"] for entry in months if entry["score"] is not None]
    trend, change = None, None
    if len(scored) >= 3:
        window = max(1, len(scored) // 3)  # compare the earliest third with the latest third
        early = sum(scored[:window]) / window
        recent = sum(scored[-window:]) / window
        change = round(recent - early)
        trend = "rising" if change >= TREND_THRESHOLD else "falling" if change <= -TREND_THRESHOLD else "steady"
    return {"months": months, "trend": trend, "change": change,
            "min_messages": MIN_MESSAGES_PER_MONTH}
