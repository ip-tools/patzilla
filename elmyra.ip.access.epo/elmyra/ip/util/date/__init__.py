# -*- coding: utf-8 -*-
# (c) 2014 Andreas Motl, Elmyra UG
import datetime

def now():
    return datetime.datetime.now()

def date_iso(date):
    return date.strftime('%Y-%m-%d')

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
