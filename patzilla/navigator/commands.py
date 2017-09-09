# -*- coding: utf-8 -*-
# (c) 2016 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
import sys
import json
from pprint import pprint

def clean_browser_database():

    # Read database file name from commandline
    dbfile = sys.argv[1]
    #print dbfile

    # Load database file
    data = json.load(file(dbfile))
    #pprint(data)

    # Purge "project" attributes from all "Query/..." objects
    for name, item in data['database'].iteritems():
        if name.startswith('Query/'):
            if 'project' in item:
                del item['project']
            #pprint(item)

    # Save database file
    print json.dumps(data, indent=4)
