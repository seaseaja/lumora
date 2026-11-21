"""Tests for patterns.py. Run from the project folder:  python -m unittest discover tests"""

import unittest
from datetime import datetime, timedelta

from patterns import (DEFAULT_KEYWORDS, NOTICE_MIN_HITS, PREVIOUS_DEFAULTS, build_dictionary,
                      count_patterns)

START = datetime(2026, 1, 1, 9)


def chat(lines):
    """lines: list of (sender, body) -> timestamped messages one minute apart."""
    return [(START + timedelta(minutes=index), sender, body) for index, (sender, body) in enumerate(lines)]


def category(result, person_index, key):
    return next(c for c in result[person_index]["categories"] if c["key"] == key)


class DictionaryTests(unittest.TestCase):
    def setUp(self):
        self.dictionary = build_dictionary()

    def test_phrases_match_as_whole_words_and_flexible_spaces(self):
        self.assertTrue(self.dictionary["criticism"].search("KAMU   SELALU gitu"))
        self.assertTrue(self.dictionary["contempt"].search("dasar lu!"))
        self.assertTrue(self.dictionary["repair"].search("maaf ya"))

    def test_everyday_words_are_not_flagged(self):
        neutral = ["aku selalu bangun pagi", "hmm oke", "gapapa kok", "ya udah besok aja",
                   "capek kuliah", "dasarnya gitu", "terserah", "tololan"]
        for text in neutral:
            for key in ("criticism", "contempt", "defensiveness", "stonewalling"):
                self.assertFalse(self.dictionary[key].search(text), f"{key!r} matched {text!r}")

    def test_database_rows_override_defaults_and_blank_rows_are_ignored(self):
        dictionary = build_dictionary([("contempt", "kampret"), ("criticism", "  "), ("unknown", "x")])
        self.assertTrue(dictionary["contempt"].search("dasar kampret"))
        self.assertFalse(dictionary["contempt"].search("bodoh"))
        self.assertTrue(dictionary["criticism"].search("kamu selalu"))  # blank row -> default kept
        self.assertNotIn("unknown", dictionary)

    def test_new_defaults_fit_the_database_column_and_replace_every_old_list(self):
        for keywords, _, _ in DEFAULT_KEYWORDS.values():
            self.assertLessEqual(len(keywords), 500)
        self.assertTrue(set(PREVIOUS_DEFAULTS) <= set(DEFAULT_KEYWORDS))


class CountPatternTests(unittest.TestCase):
    def test_counts_messages_not_phrases_per_category(self):
        result = count_patterns(chat([("A", "bodoh, goblok, tolol"), ("B", "oke")]), ["A", "B"])
        self.assertEqual(category(result, 0, "contempt")["count"], 1)

    def test_repeated_pattern_is_flagged_but_a_single_match_is_not(self):
        lines = [("A", "kamu selalu telat")] * NOTICE_MIN_HITS + [("B", "iya maaf")] * NOTICE_MIN_HITS
        result = count_patterns(chat(lines), ["A", "B"])
        self.assertTrue(category(result, 0, "criticism")["notice"])
        self.assertFalse(category(result, 1, "repair")["notice"])  # only conflict patterns are flagged

        once = count_patterns(chat([("A", "kamu selalu telat"), ("B", "oke")] * 1), ["A", "B"])
        self.assertFalse(category(once, 0, "criticism")["notice"])

    def test_rare_pattern_in_a_long_chat_is_not_flagged(self):
        lines = [("A", "kamu selalu telat")] * NOTICE_MIN_HITS + [("A", "oke")] * 1000 + [("B", "sip")]
        result = count_patterns(chat(lines), ["A", "B"])
        criticism = category(result, 0, "criticism")
        self.assertEqual(criticism["count"], NOTICE_MIN_HITS)
        self.assertFalse(criticism["notice"])

    def test_media_placeholders_are_skipped(self):
        result = count_patterns(chat([("A", "<Media omitted>"), ("A", "makasih"), ("B", "sama-sama")]), ["A", "B"])
        self.assertEqual(result[0]["text_messages"], 1)

    def test_ratio_and_its_absence(self):
        lines = [("A", "makasih"), ("A", "semangat"), ("A", "kesel"), ("B", "oke"), ("B", "makasih")]
        result = count_patterns(chat(lines), ["A", "B"])
        self.assertEqual(result[0]["ratio"], 2.0)
        self.assertIsNone(result[1]["ratio"])
        self.assertEqual(result[1]["positive_total"], 1)

    def test_people_outside_the_pair_are_ignored(self):
        result = count_patterns(chat([("A", "bodoh"), ("C", "bodoh"), ("B", "oke")]), ["A", "B"])
        self.assertEqual([row["person"] for row in result], ["A", "B"])
        self.assertEqual(category(result, 1, "contempt")["count"], 0)


if __name__ == "__main__":
    unittest.main()
