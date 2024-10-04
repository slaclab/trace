import datetime

import pytest

from main import TraceDisplay
from mixins.file_io import IOTimeParser

FAKE_TIME = datetime.datetime(2024, 6, 30)


# Pytest fixtures for timeparser and setting datetime.now()
@pytest.fixture(scope="class")
def time_parser():
    """Fixture for an instance of the IOTimeParser.

    Yields
    ------
    An instance of IOTimeParser.
    """
    yield IOTimeParser()


@pytest.fixture
def patch_datetime_now(monkeypatch):
    class mydatetime(datetime.datetime):
        @classmethod
        def now(cls):
            return FAKE_TIME

    monkeypatch.setattr(datetime, "datetime", mydatetime)


def test_export_save_file(qtrace: TraceDisplay):
    pass


def test_import_save_file(qtrace: TraceDisplay):
    pass


@pytest.mark.parametrize(
    # fmt: off
    ("given", "expected"),
    [
        (("+1d", "now"), (None,)),                                      # Relative (+) & Now          -> Exception
        (("+1d", "+1h"), (None,)),                                      # Relative (+) & Relative (+) -> Exception
        (("+1d", "-1h"), (None,)),                                      # Relative (+) & Relative (-) -> Exception
        (("+1d", "2024-06-10"), (None,)),                               # Relative (+) & Absolute     -> Exception
        (("-1d", "now"), ((2024, 6, 29), (2024, 6, 30))),               # Relative (-) & Now
        (("-1d", "+1H"), ((2024, 6, 29), (2024, 6, 29, 1))),            # Relative (-) & Relative (+)
        (("-1d", "-1H"), ((2024, 6, 29), (2024, 6, 29, 23))),           # Relative (-) & Relative (-)
        (("-1d", "2024-06-10"), ((2024, 6, 9), (2024, 6, 10))),         # Relative (-) & Absolute
        (("2024-06-10", "now"), ((2024, 6, 10), (2024, 6, 30))),        # Absolute     & Now
        (("2024-06-10", "+1d"), ((2024, 6, 10), (2024, 6, 11))),        # Absolute     & Relative (+)
        (("2024-06-10", "-1d"), ((2024, 6, 10), (2024, 6, 29))),        # Absolute     & Relative (-)
        (("2024-06-10", "2024-06-20"),((2024, 6, 10), (2024, 6, 20)))   # Absolute     & Absolute
    ],
    # fmt: on
)
def test_time_parser(patch_datetime_now, time_parser: IOTimeParser, given: tuple, expected: tuple):
    # Test that expected exceptions get raised
    if expected[0] is None:
        with pytest.raises(ValueError) as exc_info:
            start_dt, end_dt = time_parser.parse_times(*given)
        assert exc_info.type is ValueError
    else:
        # If not expecting an exception, then check start and end datetimes
        start_dt, end_dt = time_parser.parse_times(*given)
        assert start_dt == datetime.datetime(*expected[0])
        assert end_dt == datetime.datetime(*expected[1])
