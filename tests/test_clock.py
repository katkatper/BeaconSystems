import unittest

from services.clock import utc_now, utc_now_aware


class ClockTests(unittest.TestCase):
    def test_database_clock_returns_naive_utc(self):
        value = utc_now()

        self.assertIsNone(value.tzinfo)

    def test_protocol_clock_returns_timezone_aware_utc(self):
        value = utc_now_aware()

        self.assertIsNotNone(value.tzinfo)
        self.assertEqual(value.utcoffset().total_seconds(), 0)


if __name__ == "__main__":
    unittest.main()
