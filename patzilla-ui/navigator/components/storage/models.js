// -*- coding: utf-8 -*-
// (c) 2014-2018 Andreas Motl <andreas.motl@ip-tools.org>


TimestampedModelMixin = {

    defaults: {
        parent: undefined,
        created: undefined,
        modified: undefined,
    },

    // TODO: refactor to common base class or mixin
    // automatically set "created" and "modified" fields
    // automatically create model in collection
    // http://jstarrdewar.com/blog/2012/07/20/the-correct-way-to-override-concrete-backbone-methods/
    save: function(key, val, options) {

        // Handle both `"key", value` and `{key: value}` -style arguments.
        if (key == null || typeof key === 'object') {
            attrs = key;
            options = val;
        } else {
            (attrs = {})[key] = val;
        }

        options = _.extend({}, options);

        var _this = this;

        var now = timestamp();
        var isNew = this.isNew();

        var data = {};
        if (isNew) {
            data.created = now;
        }
        data.modified = now;
        this.set(data);


        //var project = this.get('project');

        var success = options.success;
        options.success = function(model, resp, options) {

            if (isNew) {

                _this.collection.create(model, {success: function() {

                    // forward "isNew" indicator via options object
                    options.isNew = isNew;

                    // FIXME: HACK ported from project/basket saving; check whether this is really required
                    _this.collection.add(model);

                    // FIXME: IMPORTANT HACK to reset project reference after it has vanished through collection.create
                    //model.set('project', project);

                    _this.trigger('saved', model, resp, options);
                    if (success) success(model, resp, options);

                }});

            } else {
                _this.trigger('saved', model, resp, options);
                if (success) success(model, resp, options);
            }
        };

        return Backbone.Model.prototype.save.call(this, attrs, options);

    },

};


SmartCollectionMixin = {

    // TODO: refactor to common base class or mixin
    get_or_create: function(attributes) {
        var model = _(this.where(attributes)).first();
        if (!model) {
            model = this.model.build(attributes, { collection: this, parsed: false });
            this.create(model, {success: function() {
                var classname = this.constructor.name;
                log(classname + '::get_or_create: SUCCESS', model);
            }});
        }
        return model;
    },

    search: function(options) {
        // "collection.where" would return an array of models, but we want to continue working with a collection.
        // https://stackoverflow.com/questions/10548685/tojson-on-backbone-collectionwhere/10549086#10549086
        var result = this.where(options);
        var resultCollection = new this.constructor.prototype(result);
        return resultCollection;
    },

};
