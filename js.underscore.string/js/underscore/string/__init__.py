from fanstatic import Library, Resource
from js.underscore import underscore

library = Library('underscore.string.js', 'resources')
underscore_string = Resource(library, 'underscore.string.min.js', debug="underscore.string.js", depends=[underscore])
