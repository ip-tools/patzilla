# -*- coding: utf-8 -*-
# (c) 2014 Andreas Motl, Elmyra UG

def shrink_list(payload):
    """Convert a list with a single item to the item, otherwise return list"""
    if len(payload) == 1:
        return payload[0]
    else:
        return payload
