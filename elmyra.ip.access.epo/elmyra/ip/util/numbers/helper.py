# -*- coding: utf-8 -*-
# (c) 2007,2014 Andreas Motl <andreas.motl@elmyra.de>
import re

"""
Generic helper functions
"""

def pad_left(data, prefix, length):
    data = str(data)
    padding = prefix * (length - len(data))
    data = padding + data
    return data

def trim_leading_zeros(number):
    re_leading_zeros = re.compile('^0*')
    number = re_leading_zeros.sub('', number)
    return number

def strip_spaces(number):
    r_invalid = re.compile('\s')
    number = r_invalid.sub('', number)
    return number

def read_numbersfile(file):
    fh = open(file, 'r')
    numbers_raw = fh.readlines()
    fh.close()
    numbers = map(lambda number: number.replace("\n", '').replace(' ', ''), numbers_raw)
    numbers = [number for number in numbers if not number.startswith('#')]
    return numbers

def fullyear_from_year(year):
    # assume for century: 78-99 => 19, otherwise => 20
    if int(year) in range(78, 100):
        century = '19'
    else:
        century = '20'
    return century + year
