"""Tests for closeness.py. Run from the project folder:  python -m unittest discover tests"""

import unittest
from datetime import datetime, timedelta

from closeness import (MIN_MESSAGES_PER_MONTH, WARM_PATTERN, _scale, closeness_by_month,
                       compute_closeness, level_for)

PEOPLE = ["A", "B"]


def conversation(start, days, per_day, reply_seconds, every=1, senders=("A", "B"), body="oke"):
    """Alternating messages: `per_day` messages on every `every`-th day, `reply_seconds` apart.

    The sender who opens the day rotates, so both people start conversations.
    """
    messages = []
    for session, day in enumerate(range(0, days, every)):
        timestamp = start + timedelta(days=day)
        for index in range(per_day):
            timestamp += timedelta(seconds=reply_seconds)
            messages.append((timestamp, senders[(index + session) % len(senders)], body))
    return messages


class ScaleAndLevelTests(unittest.TestCase):
    def test_scale_clamps_and_interpolates(self):
        self.assertEqual(_scale(0, 5, 60), 0.0)
        self.assertEqual(_scale(100, 5, 60), 1.0)
        self.assertAlmostEqual(_scale(32.5, 5, 60), 0.5)

    def test_level_boundaries(self):
        self.assertEqual(level_for(0)[0], "Distant")
        self.assertEqual(level_for(34)[0], "Distant")
        self.assertEqual(level_for(35)[0], "Casual")
        self.assertEqual(level_for(55)[0], "Close")
        self.assertEqual(level_for(74)[0], "Close")
        self.assertEqual(level_for(75)[0], "Very close")
        self.assertEqual(level_for(100)[0], "Very close")


class WarmWordTests(unittest.TestCase):
    def test_matches_warm_words_and_laughter(self):
        for text in ("makasih ya", "Terima kasih banyak", "wkwkwk", "hahaha", "semangat!", "kangen ❤"):
            self.assertTrue(WARM_PATTERN.search(text), text)

    def test_ignores_words_that_only_contain_a_warm_word(self):
        for text in ("hugo datang", "thanksgiving", "ha", "biasa aja", "ok"):
            self.assertFalse(WARM_PATTERN.search(text), text)


class ComputeClosenessTests(unittest.TestCase):
    start = datetime(2026, 1, 1, 9)

    def test_daily_balanced_fast_warm_chat_is_very_close(self):
        messages = conversation(self.start, 60, 60, reply_seconds=60, body="wkwk makasih")
        result = compute_closeness(messages, PEOPLE)
        self.assertEqual(result["level"], "Very close")
        self.assertEqual(result["score"], 100)

    def test_rare_one_sided_slow_chat_is_distant(self):
        messages = conversation(self.start, 90, 4, reply_seconds=4 * 3600, every=10,
                                senders=("A", "A", "A", "B"))
        result = compute_closeness(messages, PEOPLE)
        self.assertEqual(result["level"], "Distant")
        self.assertLess(result["score"], 35)

    def test_components_add_up_to_score_and_weights_to_100(self):
        messages = conversation(self.start, 30, 20, reply_seconds=600, every=2)
        result = compute_closeness(messages, PEOPLE)
        self.assertEqual(sum(part["weight"] for part in result["components"]), 100)
        self.assertAlmostEqual(sum(part["points"] for part in result["components"]), result["score"], delta=1)
        for part in result["components"]:
            self.assertGreaterEqual(part["value"], 0)
            self.assertLessEqual(part["value"], 1)
            self.assertTrue(part["rule"])

    def test_media_placeholders_do_not_count_as_text(self):
        messages = conversation(self.start, 10, 20, reply_seconds=60, body="<Media omitted>")
        warmth = next(part for part in compute_closeness(messages, PEOPLE)["components"] if part["key"] == "warmth")
        self.assertEqual(warmth["value"], 0)

    def test_gaps_over_six_hours_are_new_conversations_not_slow_replies(self):
        messages = [(self.start, "A", "halo"), (self.start + timedelta(hours=7), "B", "halo juga"),
                    (self.start + timedelta(hours=7, minutes=1), "A", "oke")]
        reply = next(part for part in compute_closeness(messages, PEOPLE)["components"] if part["key"] == "reply")
        self.assertEqual(reply["detail"], "Typical reply in 1 min")


class MonthlyTrendTests(unittest.TestCase):
    def test_sparse_months_are_not_scored(self):
        messages = conversation(datetime(2026, 1, 1, 9), 90, 2, reply_seconds=60, every=15)
        result = closeness_by_month(messages, PEOPLE)
        self.assertTrue(all(month["score"] is None for month in result["months"]))
        self.assertIsNone(result["trend"])

    def test_empty_month_between_active_months_is_listed(self):
        messages = (conversation(datetime(2026, 1, 1, 9), 20, 30, reply_seconds=60)
                    + conversation(datetime(2026, 3, 1, 9), 20, 30, reply_seconds=60))
        months = closeness_by_month(messages, PEOPLE)["months"]
        self.assertEqual([month["month"] for month in months], ["2026-01", "2026-02", "2026-03"])
        self.assertIsNone(months[1]["score"])
        self.assertEqual(months[1]["messages"], 0)

    def test_rising_and_falling_trends(self):
        quiet = lambda start: conversation(start, 28, 10, reply_seconds=3 * 3600, every=4)
        lively = lambda start: conversation(start, 28, 60, reply_seconds=60, body="wkwk")
        starts = [datetime(2026, month, 1, 9) for month in range(1, 7)]
        rising = [m for start in starts[:3] for m in quiet(start)] + [m for start in starts[3:] for m in lively(start)]
        falling = [m for start in starts[:3] for m in lively(start)] + [m for start in starts[3:] for m in quiet(start)]
        self.assertEqual(closeness_by_month(rising, PEOPLE)["trend"], "rising")
        self.assertEqual(closeness_by_month(falling, PEOPLE)["trend"], "falling")

    def test_steady_chat(self):
        messages = conversation(datetime(2026, 1, 1, 9), 180, 40, reply_seconds=90)
        result = closeness_by_month(messages, PEOPLE)
        self.assertEqual(result["trend"], "steady")
        self.assertLessEqual(abs(result["change"]), 2)

    def test_partial_first_month_is_judged_on_covered_days(self):
        # Chat starts on the 25th and talks every day: consistency should be full, not 7/31.
        messages = conversation(datetime(2026, 1, 25, 9), 7, MIN_MESSAGES_PER_MONTH, reply_seconds=60)
        january = closeness_by_month(messages, PEOPLE)["months"][0]
        self.assertIsNotNone(january["score"])
        full_span = compute_closeness(messages, PEOPLE)
        self.assertEqual(january["score"], full_span["score"])


if __name__ == "__main__":
    unittest.main()
