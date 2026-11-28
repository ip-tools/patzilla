import datetime

from patzilla.util.date import month_range, year_range


def test_month_range():
    start, end = month_range(datetime.date(2024, 2, 10))
    assert start.date() == datetime.date(2024, 2, 1)
    assert end.date() == datetime.date(2024, 2, 29)

    start, end = month_range(datetime.date(2023, 12, 31))
    assert start.date() == datetime.date(2023, 12, 1)
    assert end.date() == datetime.date(2023, 12, 31)


def test_year_range():
    start, end = year_range(datetime.date(2023, 6, 15))
    assert start.date() == datetime.date(2023, 1, 1)
    assert end.date() == datetime.date(2023, 12, 31)
