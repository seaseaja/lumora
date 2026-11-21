"""Communication-pattern signals based on Gottman's research, matched by keyword.

Gottman describes four patterns that predict conflict going badly (the "Four
Horsemen": criticism, contempt, defensiveness, stonewalling), repair attempts
that calm a conflict down, and a balance of positive to negative interaction.
His research observed couples talking; this module only counts phrases in a
chat export. A phrase match cannot tell a joke from an insult, so results are
"patterns worth noticing", never a judgement about a person.

`messages` is a list of (datetime, sender, body), already filtered to `people`.
"""

import re
from collections import Counter

# category -> (comma-separated phrases, source, weight). Phrases match as whole words,
# case-insensitive, and any run of spaces in a phrase matches any run of spaces.
# Single everyday words ("selalu", "hmm", "capek") are avoided on purpose: they are
# far more often neutral than critical.
DEFAULT_KEYWORDS = {
    "criticism": ("kamu selalu,kamu tuh selalu,kamu gak pernah,kamu ga pernah,kamu nggak pernah,"
                  "kamu tidak pernah,kenapa sih kamu,kamu tuh emang,gak becus,ga becus,you always,you never",
                  "Gottman (Four Horsemen)", -2),
    "contempt": ("bodoh,goblok,tolol,idiot,sok tau,sok tahu,terserah lu,dasar lu,dasar kamu,najis,"
                 "lebay banget sih,whatever lah",
                 "Gottman (Four Horsemen)", -3),
    "defensiveness": ("bukan salah aku,bukan salahku,kan kamu yang,aku udah bilang,lah kok aku,kok jadi aku,"
                      "kok aku yang disalahin,not my fault",
                      "Gottman (Four Horsemen)", -1),
    "stonewalling": ("capek ngomong,males ngomong,males bahas,gak usah dibahas,ga usah dibahas,"
                     "udah lah terserah,terserah deh,terserah kamu aja,gak mau bahas,ga mau bahas",
                     "Gottman (Four Horsemen)", -1),
    "repair": ("maaf,maafin,sorry,sori,aku salah,my bad,yuk baikan,jangan marah ya,aku ngerti kok",
               "Gottman (repair attempts)", 2),
    "positive": ("makasih,terima kasih,thanks,sayang,seneng,senang,keren,bangga,mantap,kangen,"
                 "hati-hati ya,semangat,love you,proud of you",
                 "Rasio positif:negatif", 1),
    "negative": ("kesel,kesal,benci,bete,kecewa,sebel,marah,muak",
                 "Rasio positif:negatif", -1),
}
# The first seed shipped these lists. seed.py upgrades a row only while it still
# holds this exact text, so a dictionary someone has edited is never overwritten.
PREVIOUS_DEFAULTS = {
    "criticism": "selalu,tidak pernah,kamu tuh,kenapa sih kamu,gak becus",
    "contempt": "bodoh,males ah,terserah lu,dasar,sok tau",
    "defensiveness": "bukan salah aku,kan kamu yang,aku udah bilang,lah kok aku",
    "stonewalling": "terserah,ya udah,hmm,gapapa,capek ngomong",
    "positive": "makasih,sayang,seneng,keren,bangga,mantap,kangen,hati-hati ya",
    "negative": "kesel,benci,males,bete,capek,kecewa",
}

HORSEMEN = ("criticism", "contempt", "defensiveness", "stonewalling")
CATEGORY_INFO = {
    "criticism": ("Criticism", "Complaints framed as a flaw in the other person (\"you always…\")."),
    "contempt": ("Contempt", "Insults, name-calling, or mockery. Friends often use these words as jokes."),
    "defensiveness": ("Defensiveness", "Turning a complaint back or denying any part in it."),
    "stonewalling": ("Stonewalling", "Shutting a conversation down instead of continuing it."),
    "repair": ("Repair attempts", "Apologies and attempts to calm things down."),
    "positive": ("Positive wording", "Thanks, affection, encouragement, praise."),
    "negative": ("Negative wording", "Annoyance, disappointment, anger."),
}
# A Horsemen category is flagged as worth noticing for a person only when it is both
# repeated and not drowned in a long chat: at least this many matches...
NOTICE_MIN_HITS = 3
# ...and at least this many matches per 100 of that person's text messages.
NOTICE_MIN_RATE = 0.5
MEDIA_PATTERN = re.compile(r"omitted|tidak disertakan|was deleted|telah dihapus", re.I)


def build_dictionary(rows=None):
    """Compile {category: regex}. rows are (category, keywords) pairs, e.g. from the
    chat_keywords table; categories missing from rows fall back to DEFAULT_KEYWORDS."""
    phrases = {category: keywords for category, (keywords, _, _) in DEFAULT_KEYWORDS.items()}
    for category, keywords in rows or ():
        if category in CATEGORY_INFO and keywords and keywords.strip():
            phrases[category] = keywords
    compiled = {}
    for category, keywords in phrases.items():
        terms = [term.strip() for term in keywords.split(",") if term.strip()]
        if terms:
            alternatives = "|".join(r"\s+".join(map(re.escape, term.split())) for term in sorted(terms, key=len, reverse=True))
            compiled[category] = re.compile(rf"(?<!\w)(?:{alternatives})(?!\w)", re.I)
    return compiled


def count_patterns(messages, people, dictionary=None):
    """Count, per person, how many text messages contain each category's phrases.

    A message counts once per category however many phrases it contains.
    """
    dictionary = dictionary or build_dictionary()
    hits = {person: Counter() for person in people}
    text_counts = Counter()
    for _, sender, body in messages:
        if sender not in hits or MEDIA_PATTERN.search(body):
            continue
        text_counts[sender] += 1
        for category, pattern in dictionary.items():
            if pattern.search(body):
                hits[sender][category] += 1

    result = []
    for person in people:
        texts = text_counts[person]
        own = hits[person]
        categories = []
        for category in CATEGORY_INFO:
            if category not in dictionary:
                continue
            count = own[category]
            rate = round(count * 100 / texts, 2) if texts else 0.0
            label, description = CATEGORY_INFO[category]
            categories.append({"key": category, "label": label, "description": description,
                               "count": count, "per_100": rate,
                               "notice": category in HORSEMEN and count >= NOTICE_MIN_HITS and rate >= NOTICE_MIN_RATE})
        negative_total = own["negative"] + sum(own[category] for category in HORSEMEN)
        positive_total = own["positive"] + own["repair"]
        result.append({
            "person": person, "text_messages": texts, "categories": categories,
            "positive_total": positive_total, "negative_total": negative_total,
            # None when there is nothing negative to divide by; the template says so in words.
            "ratio": round(positive_total / negative_total, 1) if negative_total else None,
        })
    return result
