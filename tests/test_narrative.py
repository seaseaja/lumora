"""The AI narrative prompt carries the closeness and pattern results.

The AI provider is replaced with a stub, so no request leaves the machine.
Run from the project folder:  python -m unittest discover tests
"""

import json
import os
import unittest
from datetime import datetime, timedelta
from unittest import mock

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-only")

import main  # noqa: E402
from closeness import closeness_by_month, compute_closeness  # noqa: E402
from patterns import count_patterns  # noqa: E402

PEOPLE = ["Real Name A", "Real Name B"]
ALIASES = ["Me", "Them"]


def sample_chat():
    messages, timestamp = [], datetime(2026, 1, 1, 9)
    for day in range(70):
        timestamp = datetime(2026, 1, 1, 9) + timedelta(days=day)
        for index in range(30):
            timestamp += timedelta(minutes=2)
            body = "kamu selalu telat" if index % 5 == 0 else "makasih ya"
            messages.append((timestamp, PEOPLE[(index + day) % 2], body))
    return messages


def chart_for(messages):
    patterns = count_patterns(messages, PEOPLE)
    for row in patterns:
        row["person"] = dict(zip(PEOPLE, ALIASES))[row["person"]]
    closeness = compute_closeness(messages, PEOPLE)
    closeness["monthly"] = closeness_by_month(messages, PEOPLE)
    return {"first_date": "2026-01-01", "last_date": "2026-03-11", "people": [], "communication_metrics": [],
            "monthly_activity": [{"month": "2026-01"}], "topics": [], "closeness": closeness, "patterns": patterns}


class NarrativeScoresTests(unittest.TestCase):
    def test_scores_are_compact_and_use_aliases(self):
        chart = chart_for(sample_chat())
        context = main.narrative_scores(chart)
        self.assertEqual(context["rule_based_closeness"]["level"], chart["closeness"]["level"])
        self.assertEqual(len(context["rule_based_closeness"]["components"]), 6)
        self.assertEqual([row["person"] for row in context["keyword_communication_patterns"]], ALIASES)
        self.assertNotIn("Real Name", json.dumps(context))

    def test_old_reports_without_scores_give_an_empty_context(self):
        self.assertEqual(main.narrative_scores({}), {})

    def test_prompt_sent_to_ai_includes_scores_and_rules(self):
        messages = sample_chat()
        chart = chart_for(messages)
        reply = json.dumps({"overview": "ok", "topics": [], "connections": [], "monthly": [],
                            "strengths": [], "cautions": []})
        with mock.patch.object(main, "call_openai", return_value=reply) as fake_ai:
            main.build_chat_narrative(messages, PEOPLE, ALIASES, chart)
        instructions, prompt, _ = fake_ai.call_args.args
        sent = json.loads(prompt)
        self.assertEqual(sent["rule_based_closeness"]["score_out_of_100"], chart["closeness"]["score"])
        self.assertIn("keyword_communication_patterns", sent)
        self.assertIn("never call anyone a red flag", instructions)
        self.assertIn("do not state a different closeness level", instructions)


if __name__ == "__main__":
    unittest.main()
