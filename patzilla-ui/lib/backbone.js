// -*- coding: utf-8 -*-
// (c) 2014-2018 Andreas Motl <andreas.motl@ip-tools.org>
'use strict';

export { SmartCollectionMixin };


// Utility: Easy multiple-inheritance in Backbone.js
// https://gist.github.com/alassek/1227770
(function () {

  function extendEach () {
    var args  = Array.prototype.slice.call(arguments),
        child = this;

    _.each(args, function (proto) {
      child = child.extend(proto);
    });

    return child;
  }

  Backbone.Model.extendEach        =
    Backbone.Collection.extendEach =
    Backbone.Router.extendEach     =
    Backbone.View.extendEach       = extendEach;

})();


const SmartModelMixin = {
    /*
    This supports the SmartCollectionMixin in supporting us re. DWIM.

    SmartModelMixin automatically adds models it its corresponding
    collection when saving it.

    SmartModelMixin optionally maintains two model attributes
    "created" and "modified" on behalf of you. To enable this,
    just set its "timestamped" option to a truthy value.
    */

    // http://jstarrdewar.com/blog/2012/07/20/the-correct-way-to-override-concrete-backbone-methods/
    save: function(key, val, options) {

        //log('SmartModelMixin::save', key, val, options);
        var attrs, method, xhr, attributes = this.attributes;

        // Handle both `"key", value` and `{key: value}` -style arguments.
        if (key == null || typeof key === 'object') {
            attrs = key;
            options = val;
        } else {
            (attrs = {})[key] = val;
        }

        options = _.extend({}, options);

        var isNew = this.isNew();


        // Optionally apply timestamping
        if (this.timestamped) {
            var now = timestamp();
            var data = {};
            if (isNew) {
                data.created = now;
            }
            data.modified = now;
            this.set(data);
        }

        //var project = this.get('project');

        var _this = this;
        var success = options.success;
        options.success = function(model, resp, options) {

            if (isNew) {

                _this.collection.create(model, {success: function() {

                    // Forward "isNew" indicator via options object
                    options.isNew = isNew;

                    // FIXME: HACK ported from project/basket saving; check whether this is really required
                    _this.collection.add(model);

                    // FIXME: IMPORTANT HACK to reset project reference after it has vanished through collection.create
                    //model.set('project', project);

                    _this.trigger('x-saved', model, resp, options);
                    if (success) success(model, resp, options);

                }});

            } else {
                _this.trigger('x-saved', model, resp, options);
                if (success) success(model, resp, options);
            }
        };

        //this.trigger('before:save', model, resp, options);

        return Backbone.Model.prototype.save.call(this, attrs, options);

    },

};


const SmartCollectionMixin = {

    by_key: function(key) {
        //log('SmartCollectionMixin::by_key', key);
        return this.get_or_create({key: key});
    },

    get_or_create: function(attributes) {
        var model = _(this.where(attributes)).first();
        if (!model) {
            model = this.model.build(attributes, { collection: this, parsed: false });
            /*
            var _this = this;
            this.create(model, {success: function() {
                var classname = _this.constructor.name;
                log(classname + '::get_or_create: SUCCESS', model);
            }});
            */
        }

        _.extend(model, SmartModelMixin);

        return model;
    },

    search: function(options, collection_factory) {
        // While "collection.where" would return an array of models,
        // but we intend to continue working with a Backbone collection.
        // https://stackoverflow.com/questions/10548685/tojson-on-backbone-collectionwhere/10549086#10549086
        var result = this.where(options);
        var resultCollection = new collection_factory(result);
        return resultCollection;
    },

};
