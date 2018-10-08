# -*- coding: utf-8 -*-
# (c) 2014-2017 Andreas Motl, Elmyra UG
import ago
import arrow
import logging
import datetime
from arrow.arrow import Arrow
from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def now():
    return datetime.datetime.now()

def date_iso(date):
    return Arrow.fromdatetime(date).format('YYYY-MM-DD')

def date_iso_compact(date):
    return Arrow.fromdatetime(date).format('YYYYMMDD')

def date_german(date):
    return Arrow.fromdatetime(date).format('DD.MM.YYYY')

def from_german(date):
    return Arrow.strptime(date, '%d.%m.%Y')

def german_to_iso(date, graceful=False):
    try:
        date = from_german(date)
    except ValueError:
        if not graceful:
            raise
        date = parse_date_iso(date)
    return date_iso(date)

def parse_date_universal(datestring):
    formats = [
        '%d.%m.%Y',     # german
        '%Y-%m-%d',     # ISO
        '%Y%m%d',       # ISO, compact
        '%Y-%m',        # ISO
        '%Y',           # Year only
    ]
    for format in formats:
        logger.debug("Trying to parse date '{}' with format '{}'".format(datestring, format))
        try:
            parsed = Arrow.strptime(datestring, format)
            logger.debug("Successfully parsed date '{}' with format '{}': {}".format(datestring, format, parsed))
            return parsed
        except:
            pass

def datetime_iso(date):
    return date.strftime('%Y-%m-%d %H:%M:%S')

def datetime_iso_filename(date):
    return date.strftime('%Y-%m-%d_%H-%M-%S')

def datetime_isoformat(date, microseconds=False):
    if not microseconds:
        date = date - datetime.timedelta(microseconds=date.microsecond)
    return date.isoformat()

def today_iso():
    return date_iso(now())

def week_iso():
    return now().strftime('%YW%W')

def month_iso():
    return now().strftime('%Y-%m')

def year():
    return now().strftime('%Y')

def parse_dateweek(datestring, weekday):
    return datetime.datetime.strptime(datestring + str(weekday), '%YW%W%w')

def parse_weekrange(datestring):
    # parses e.g. 2011W22 to (2011, 5, 30) - (2011, 6, 5)
    # see also: http://stackoverflow.com/questions/5882405/get-date-from-iso-week-number-in-python
    payload  = {
        'begin': parse_dateweek(datestring, 1),
        'end': parse_dateweek(datestring, 0),
    }
    return payload

def parse_date_iso(isodate):
    return datetime.datetime.strptime(isodate, '%Y-%m-%d')

def unixtime_to_datetime(unixtime):
    return datetime.datetime.fromtimestamp(unixtime)

def unixtime_to_human(unixtime):
    return ago.human(unixtime_to_datetime(unixtime))

def iso_to_german(date):
    if '-' in date:
        date = date_german(parse_date_universal(date))
    return date

def iso_to_iso_compact(date):
    if '-' in date:
        date = date_iso_compact(parse_date_iso(date))
    return date

def parse_date_within(value):
    """
    parses a date range expression like "within 2014-01-01,2014-01-31"
    """
    value = value.replace('within', '').strip().strip('"')
    parts = value.split(',')
    parts = map(unicode.strip, parts)
    result = {
        'startdate': parts[0],
        'enddate': parts[1],
    }
    return result

def year_range_to_within(value):
    """
    Parse year ranges like "1990-2014" or "1990 - 2014"
    and convert into "within 1990,2014" expression
    """
    if value.count(u'-') == 1:
        parts = value.split(u'-')
        parts = [part.strip() for part in parts]
        year_from, year_to = parts
        if len(year_from) == 4 and len(year_to) == 4:
            value = u'within {year_from},{year_to}'.format(**locals())
    return value

def week_range(date):
    """
    Find the first & last day of the week for the given day.
    Assuming weeks start on Monday and end on Sunday.

    Returns a tuple of ``(start_date, end_date)``.

    Original version (used US week definition from Sunday to Saturday)
    https://bradmontgomery.net/blog/2013/03/07/calculate-week-range-date/
    https://gist.github.com/bradmontgomery/5110985

    See also:
    http://code.activestate.com/recipes/521915-start-date-and-end-date-of-given-week/
    https://stackoverflow.com/questions/2003841/how-can-i-get-the-current-week-using-python
    """
    # isocalendar calculates the year, week of the year, and day of the week.
    # dow is Mon = 1, Sat = 6, Sun = 7
    year, week, dow = date.isocalendar()

    # Find the first day of the week.
    start_date = date - datetime.timedelta(dow - 1)

    # Now, add 6 for the last day of the week (i.e., count up to Sunday)
    end_date = start_date + datetime.timedelta(6)

    return (start_date, end_date)

def month_range(date):

    # https://stackoverflow.com/questions/42950/get-last-day-of-the-month-in-python/27667421#27667421
    start_date = datetime.datetime(date.year, date.month, 1)
    end_date = start_date + relativedelta(months=1, days=-1)

    start_date = Arrow.fromdatetime(start_date)
    end_date = Arrow.fromdatetime(end_date)

    return (start_date, end_date)

def year_range(date):

    start_date = datetime.datetime(date.year, 1, 1)
    end_date   = datetime.datetime(date.year, 12, 31)

    start_date = Arrow.fromdatetime(start_date)
    end_date = Arrow.fromdatetime(end_date)

    return (start_date, end_date)


def humanize_date_english(datestring):
    date = arrow.get(datestring)
    date = date.format('MMMM DD, YYYY') + ' at ' + date.format('HH:mm')
    return date

