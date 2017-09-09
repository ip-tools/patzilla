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

def purge_projects(data):
    # Purge "project" attributes from all "Query/..." objects
    for name, item in data['database'].iteritems():
        if name.startswith('Query/'):
            if 'project' in item:
                del item['project']
            #pprint(item)


def main():

    # Read database file name from commandline
    jsonfile = sys.argv[1]

    # Load database file
    data = json.load(file(jsonfile))

    strip_titles(data)
    #purge_projects(data)

    # Save database file
    print json.dumps(data, indent=4)


if __name__ == '__main__':
    main()
