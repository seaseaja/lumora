import unittest
from datetime import date

from lunar_new_year import FIRST_YEAR, LAST_YEAR, IMLEK_DATES, lunar_new_year


def shio_year(born: date) -> int:
    return born.year if born >= lunar_new_year(born.year) else born.year - 1


SHIO = ["Rat", "Ox", "Tiger", "Rabbit", "Dragon", "Snake", "Horse", "Goat", "Monkey", "Rooster", "Dog", "Pig"]


def shio_name(born: date) -> str:
    return SHIO[(shio_year(born) - 2020) % 12]


class LunarNewYearTest(unittest.TestCase):
    def test_covers_every_year_from_1900(self):
        self.assertEqual(FIRST_YEAR, 1900)
        self.assertGreaterEqual(LAST_YEAR, 2030)
        self.assertEqual(sorted(IMLEK_DATES), list(range(FIRST_YEAR, LAST_YEAR + 1)))

    def test_dates_fall_between_21_january_and_20_february(self):
        for year, day in IMLEK_DATES.items():
            self.assertTrue(date(year, 1, 21) <= day <= date(year, 2, 20), year)

    def test_years_before_1991_now_resolve(self):
        # 1983 used to fail with "Lunar calendar data is unavailable".
        self.assertEqual(lunar_new_year(1983), date(1983, 2, 13))
        self.assertEqual(shio_name(date(1983, 2, 12)), "Dog")
        self.assertEqual(shio_name(date(1983, 2, 13)), "Pig")
        self.assertEqual(shio_name(date(1990, 1, 10)), "Snake")
        self.assertEqual(shio_name(date(1990, 1, 27)), "Horse")
        self.assertEqual(shio_name(date(1900, 1, 1)), "Pig")

    def test_known_recent_years(self):
        self.assertEqual(shio_name(date(2024, 2, 9)), "Rabbit")
        self.assertEqual(shio_name(date(2024, 2, 10)), "Dragon")
        self.assertEqual(shio_name(date(2026, 2, 17)), "Horse")


if __name__ == "__main__":
    unittest.main()
