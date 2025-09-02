import datetime
from re import compile

from trace.config import logger


class IOTimeParser:
    """Collection of classmethods to parse a given date time string. The
    string can contain an absolute date and time, or a date and time that
    are relative to another time or even each other.
    """

    full_relative_re = compile(r"^([+-]?\d+[yMwdHms] ?)*\s*((?:[01]\d|2[0-3])(?::[0-5]\d)(?::[0-5]\d(?:.\d*)?)?)?$")
    full_absolute_re = compile(r"^\d{4}-[01]\d-[0-3]\d\s*((?:[01]\d|2[0-3])(?::[0-5]\d)(?::[0-5]\d(?:.\d*)?)?)?$")

    relative_re = compile(r"(?<!\S)(?:[+-]?\d+[yMwdHms])")
    date_re = compile(r"^\d{4}-[01]\d-[0-3]\d")
    time_re = compile(r"(?:[01]\d|2[0-3])(?::[0-5]\d)(?::[0-5]\d(?:.\d*)?)?")

    @classmethod
    def is_relative(cls, input_str: str) -> bool:
        """Check if the given string is a relative time (e.g. '+1d',
        '-8h', '-1w 08:00')

        Parameters
        ---------
        input_str : str

        """
        found = cls.full_relative_re.fullmatch(input_str)
        return bool(found)

    @classmethod
    def is_absolute(cls, input_str: str) -> bool:
        """Check if the given string is an absolute time (e.g.
        '2024-07-16 08:00')
        """
        found = cls.full_absolute_re.fullmatch(input_str)
        return bool(found)

    @classmethod
    def relative_to_delta(cls, time: str) -> datetime.timedelta:
        """Convert the given string containing a relative time into a
        datetime.timedelta

        Parameters
        ----------
        time : str
            String consisting of a time in a relative format (e.g. '-1d')

        Returns
        -------
        datetime.timedelta
            A duration expressing the difference between two datetimes
        """
        td = datetime.timedelta()
        negative = True
        for token in cls.relative_re.findall(time):
            logger.debug(f"Processing relative time token: {token}")
            if token[0] in "+-":
                negative = token[0] == "-"
            elif negative:
                token = "-" + token
            number = int(token[:-1])

            unit = token[-1]
            if unit == "s":
                td += datetime.timedelta(seconds=number)
            elif unit == "m":
                td += datetime.timedelta(minutes=number)
            elif unit == "H":
                td += datetime.timedelta(hours=number)
            elif unit == "w":
                td += datetime.timedelta(weeks=number)
            elif unit in "yMd":
                if unit == "y":
                    number *= 365
                elif unit == "M":
                    number *= 30
                td += datetime.timedelta(days=number)
        logger.debug(f"Relative time '{time}' as delta: {td}")
        return td

    @classmethod
    def set_time_on_datetime(cls, dt: datetime.datetime, time_str: str) -> datetime.datetime:
        """Set an absolute time on a datetime object

        Parameters
        ----------
        dt : datetime
            The datetime to alter
        time_str : str
            The string containing the new time to set (e.g. '-1d 15:00')

        Returns
        -------
        datetime
            The datetime object with the same date and the new time
        """
        # Get absolute time from string, return datetime if none
        try:
            time = cls.time_re.search(time_str).group()
        except AttributeError:
            return dt

        if time.count(":") == 1:
            time += ":00"
        h, m, s = map(int, map(float, time.split(":")))
        dt = dt.replace(hour=h, minute=m, second=s)

        return dt

    @classmethod
    def parse_times(cls, start_str: str, end_str: str) -> tuple[datetime.datetime, datetime.datetime]:
        """Convert 2 strings containing a start and end date & time, return the
        values' datetime objects. The strings can be formatted as either absolute
        times or relative times. Both are needed as relative times may be relative
        to the other time.

        Parameters
        ----------
        start_str : str
            The leftmost time the x-axis of the plot should show
        end_str : str
            The rigthmost time the x-axis of the plot should show, should be >start

        Returns
        -------
        tuple[datetime, datetime]
            The python datetime objects for the exact start and end datetimes referenced

        Raises
        ------
        ValueError
            One of the given strings is in an incorrect format
        """
        start_dt = start_delta = None
        end_dt = end_delta = None
        basetime = datetime.datetime.now()

        # Process the end time string first to determine
        # if the basetime is the start time, end time, or 'now'
        if end_str == "now":
            end_dt = basetime
        elif cls.is_relative(end_str):
            end_delta = cls.relative_to_delta(end_str)

            # end_delta >= 0 --> the basetime is start time, so are processed after the start time
            # end_delta <  0 --> the basetime is 'now'
            if end_delta < datetime.timedelta():
                end_dt = basetime + end_delta
                end_dt = cls.set_time_on_datetime(end_dt, end_str)
        elif cls.is_absolute(end_str):
            end_dt = datetime.datetime.fromisoformat(end_str)
            basetime = end_dt
        else:
            raise ValueError("Time Axis end value is in an unexpected format.")

        # Process the start time string second, it may be used as the basetime
        if cls.is_relative(start_str):
            start_delta = cls.relative_to_delta(start_str)

            # start_delta >= 0 --> raise ValueError; this isn't allowed
            if start_delta < datetime.timedelta():
                start_dt = basetime + start_delta
                start_dt = cls.set_time_on_datetime(start_dt, start_str)
            else:
                raise ValueError("Time Axis start value cannot be a relative time and be positive.")
        elif cls.is_absolute(start_str):
            start_dt = datetime.datetime.fromisoformat(start_str)
        else:
            raise ValueError("Time Axis start value is in an unexpected format.")

        # If the end time is relative and end_delta >= 0 --> start time is the base
        if end_delta and end_delta >= datetime.timedelta():
            basetime = start_dt
            end_dt = end_delta + basetime
            end_dt = cls.set_time_on_datetime(end_dt, end_str)

        return (start_dt, end_dt)
