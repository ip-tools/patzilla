#!/home/frank/DATA/Envs/env1/bin/python3
# -*- coding: utf-8 -*-
import regex as re
import sys

from pyramid.scripts.pserve import main

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit(main())
