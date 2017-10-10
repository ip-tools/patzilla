# -*- coding: utf-8 -*-
# (c) 2013-2016 Andreas Motl, Elmyra UG
import simplejson as json

def json_pretty_renderer(helper):
    return _JsonPrettyRenderer()

class _JsonPrettyRenderer(object):
    def __call__(self, data, context):
        response = context['request'].response
        response.content_type = 'application/json'
        return json.dumps(data, use_decimal=True, sort_keys=True, indent=4)

class XmlRendererTest(object):
    def __call__(self, data, context):
        acceptable = ('application/json', 'text/json', 'text/plain')
        response = context['request'].response
        content_type = (context['request'].accept.best_match(acceptable)
                        or acceptable[0])
        response.content_type = content_type
        print "data:", data
        return 'hello'
        #return json.dumps(data, use_decimal=True)

class XmlRenderer(object):

    def __init__(self, info):
        pass

    def __call__(self, data, context):
        request = context.get('request')
        if request is not None:
            response = request.response
            response.content_type = 'text/xml'
        return data

class PngRenderer(object):

    def __init__(self, info):
        pass

    def __call__(self, data, context):
        request = context.get('request')
        if request is not None:
            response = request.response
            response.content_type = 'image/png'
        return data

class PdfRenderer(object):

    def __init__(self, info):
        pass

    def __call__(self, data, context):
        request = context.get('request')
        if request is not None:
            response = request.response
            response.content_type = 'application/pdf'
        return data

class NullRenderer(object):

    def __init__(self, info):
        pass

    def __call__(self, data, context):
        request = context.get('request')
        return data
