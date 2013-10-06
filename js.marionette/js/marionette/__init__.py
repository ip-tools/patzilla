from fanstatic import Library, Resource
from js.backbone import backbone
from js.jquery import jquery
from js.underscore import underscore
from js.json2 import json2

library = Library('backbone.marionette.js', 'resources')
marionette = Resource(library, 'backbone.marionette.min.js', debug="backbone.marionette.js", depends=[backbone, jquery, underscore, json2])
