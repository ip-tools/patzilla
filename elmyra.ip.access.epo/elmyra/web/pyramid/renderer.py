# -*- coding: utf-8 -*-
# (c) 2014 Andreas Motl, Elmyra UG
import simplejson as json

def json_pretty_renderer(helper):
    return _JsonPrettyRenderer()

class _JsonPrettyRenderer(object):
    def __call__(self, data, context):
        response = context['request'].response
        response.content_type = 'application/json'
        return json.dumps(data, use_decimal=True, sort_keys=True, indent=4)
