#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) 2015-2017 Andreas Motl, Elmyra UG
import sys
import json
"""
Synopsis::

    python patzilla/navigator/tools/browser_database_tool.py var/tmp/cdb/01-original.json | jq . > var/tmp/cdb/02-notitles.json

"""

def purge_titles(data):
    # Purge "title" attributes from BasketEntry objects
    for name, entity in data['database'].items():
        if name.startswith('BasketEntry'):
            if 'title' in entity:
                del entity['title']
            if 'number' in entity:
                entity['number'] = entity['number'].strip('★ ')

def purge_numbers_seen(data):
    # Purge all BasketEntry objects with "seen==true"
    keys = []
    for name, item in data['database'].items():
        if name.startswith('BasketEntry/'):
            if 'seen' in item and item['seen'] == True:
                keys.append(name)

    for key in keys:
        del data['database'][key]

def purge_projects(data):
    # Purge "project" attributes from all "Query/..." objects
    for name, item in data['database'].items():
        if name.startswith('Query/'):
            if 'project' in item:
                del item['project']
            #pprint(item)

def main():

    # Read database file name from commandline
    jsonfile = sys.argv[1]

    # Load database file
    data = json.load(file(jsonfile))

    #purge_titles(data)
    purge_numbers_seen(data)
    #purge_projects(data)

    # Save database file
    print(json.dumps(data, indent=4))


if __name__ == '__main__':
    main()
