import pytest
from utils.date_utils import next_weekday, parse_date_string
from datetime import datetime


def test_parse_iso_date():
    assert parse_date_string("2025-07-24", datetime(2025, 7, 23)) == "2025-07-24"


def test_parse_tomorrow():
    base = datetime(2025, 7, 23)
    assert parse_date_string("tomorrow", base) == "2025-07-24"


@pytest.mark.parametrize(
    "weekday_name, from_date, expected",
    [
        ("Friday", datetime(2025, 7, 23), "2025-07-25"),  # Wed -> Fri
        ("Wednesday", datetime(2025, 7, 23), "2025-07-30"),  # Wed -> next Wed
    ],
)
def test_parse_and_next_weekday(weekday_name, from_date, expected):
    assert next_weekday(weekday_name, from_date).strftime("%Y-%m-%d") == expected
    assert parse_date_string(weekday_name, from_date) == expected


def test_invalid_date_string():
    with pytest.raises(ValueError):
        parse_date_string("notaday", datetime.now())


def test_invalid_weekday():
    with pytest.raises(ValueError):
        next_weekday("Funday", datetime.now())
