from fanstatic import Library, Resource
from js.jquery import jquery

library = Library('jquery.shorten.js', 'resources')
jquery_shorten = Resource(library, 'jquery.shorten.1.0.js', depends=[jquery])
