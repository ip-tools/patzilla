#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) 2015 Andreas Motl, Elmyra UG
import sys
import json
"""
Synopsis::

    ./bin/browser_database_tool.py var/tmp/cdb/01-original.json | jq . > var/tmp/cdb/02-notitles.json

"""

def strip_titles(data):
    for name, entity in data['database'].iteritems():
        if name.startswith('BasketEntry'):
            if 'title' in entity:
                del entity['title']
            if 'number' in entity:
                entity['number'] = entity['number'].strip(u'★ ')

def main():
    jsonfile = sys.argv[1]
    data = json.load(file(jsonfile))
    strip_titles(data)
    print json.dumps(data)

if __name__ == '__main__':
    main()
