
import unittest
from datetime import datetime, timedelta

from src.status import get_evaluation_status


class EvaluationStatusTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 20, 12, 0, 0)

    def test_completed_takes_priority_over_deadline(self):
        deadline = self.now - timedelta(days=1)
        self.assertEqual(
            get_evaluation_status(deadline, True, self.now),
            "Completed",
        )

    def test_past_deadline_is_closed(self):
        deadline = self.now - timedelta(seconds=1)
        self.assertEqual(
            get_evaluation_status(deadline, False, self.now),
            "Closed",
        )

    def test_less_than_24_hours_is_due_soon(self):
        deadline = self.now + timedelta(hours=2)
        self.assertEqual(
            get_evaluation_status(deadline, False, self.now),
            "Due soon",
        )

    def test_exactly_24_hours_is_active(self):
        deadline = self.now + timedelta(hours=24)
        self.assertEqual(
            get_evaluation_status(deadline, False, self.now),
            "Active",
        )

    def test_more_than_24_hours_is_active(self):
        deadline = self.now + timedelta(days=3)
        self.assertEqual(
            get_evaluation_status(deadline, False, self.now),
            "Active",
        )

    def test_deadline_as_string(self):
        deadline = "2026-10-20 14:00:00"
        self.assertEqual(
            get_evaluation_status(deadline, False, self.now),
            "Due soon",
        )


if __name__ == "__main__":
    unittest.main()
