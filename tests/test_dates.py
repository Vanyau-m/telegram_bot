import unittest
from zoneinfo import ZoneInfo

from app.utils.dates import parse_slot_input


class DatesTest(unittest.TestCase):
    def test_parses_documented_slot_format(self):
        timezone = ZoneInfo("Europe/Moscow")
        start, end = parse_slot_input(
            "15.08.2027 10:00-11:30", timezone
        )
        self.assertEqual(start.hour, 10)
        self.assertEqual(end.hour, 11)
        self.assertEqual(end.minute, 30)
        self.assertEqual(start.tzinfo, timezone)

    def test_rejects_reverse_interval(self):
        with self.assertRaises(ValueError):
            parse_slot_input(
                "15.08.2027 12:00-11:30", ZoneInfo("Europe/Moscow")
            )


if __name__ == "__main__":
    unittest.main()

