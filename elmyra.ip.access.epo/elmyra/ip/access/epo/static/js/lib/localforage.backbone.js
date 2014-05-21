/*!
 localForage Backbone Adapter
 Version 0.4.0
 https://github.com/mozilla/localforage-backbone
 (c) 2014 Mozilla, Apache License 2.0
 */
// backbone.localforage allows users of Backbone.js to store their collections
// entirely offline with no communication to a REST server. It uses whatever
// driver localForage is set to use to store the data (IndexedDB, WebSQL, or
// localStorage, depending on availability). This allows apps on Chrome,
// Firefox, IE, and Safari to use async, offline storage, which is cool.
//
// The basics of how to use this library is that it lets you override the
// `sync` method on your collections and models to use localForage. So
//
//     var MyModel = Backbone.Model.extend({})
//     var MyCollection = Backbone.Collection.extend({
//         model: MyModel
//     });
//
// becomes
//
//     var MyModel = Backbone.Collection.extend({
//         sync: Backbone.localforage.sync('ModelNamespace')
//     });
//     var MyCollection = Backbone.Collection.extend({
//         model: MyModel,
//         sync: Backbone.localforage.sync('MyCollection')
//     });
//
// Inspiration for this file comes from a few backbone.localstorage
// implementations.
(function (root, factory) {
    if (typeof define === 'function' && define.amd) {
        define(['localforage', 'backbone', 'underscore'], factory);
    } else if (typeof module !== 'undefined' && module.exports) {
        var localforage = require('localforage');
        var Backbone = require('backbone');
        var _ = require('underscore');
        module.exports = factory(localforage, Backbone, _);
    } else {
        factory(root.localforage, root.Backbone, root._);
    }
}(this, function (localforage, Backbone, _) {
    function S4() {
        return ((1 + Math.random()) * 65536 | 0).toString(16).substring(1);
    }

    function guid() {
        return S4() + S4() + "-" + S4() + "-" + S4() + "-" + S4() + "-" + S4() + S4() + S4();
    }

    // For now, we aren't complicated: just set a property off Backbone to
    // serve as our export point.
    Backbone.localforage = {
        sync: function(name) {
            var _this = this;
            var sync = function(method, model, options) {
                // If `this` is a `Backbone.Collection` it means
                // `Backbone.Collection#fetch` has been called.
                if (this instanceof Backbone.Collection) {
                    // If there's no localforageKey for this collection, create
                    // it.
                    if (!this.sync.localforageKey) {
                        this.sync.localforageKey = name;
                    }
                } else { // `this` is a `Backbone.Model` if not a `Backbone.Collection`.
                    // Generate an id if one is not set yet.
                    // TODO: Fix this to use `Backbone.Model#idAttribute`.
                    if (!model.id) {
                        model.id = model.attributes.id = guid();
                    }

                    // If there's no localforageKey for this model create it
                    if (!model.sync.localforageKey) {
                        model.sync.localforageKey = name + "/" + model.id;
                    }
                }
                switch (method) {
                    case "read":
                        return model.id ? _this.find(model, options) : _this.findAll(model, options);
                    case "create":
                        return _this.create(model, options);
                    case "update":
                        return _this.update(model, options);
                    case "delete":
                        return _this.destroy(model, options);
                }
            };

            // This needs to be exposed for later usage, but it's private to
            // the adapter.
            sync._localforageNamespace = name;

            return sync;
        },

        save: function(model, callback) {
            localforage.setItem(model.sync.localforageKey, model.toJSON(), function(data) {
                // If this model has a collection, keep the collection in =
                // sync as well.
                if (model.collection) {
                    var collection = model.collection;
                    // Create an array of `model.collection` models' ids.
                    var collectionData = collection.map(function(model) {
                        return collection.model.prototype.sync._localforageNamespace + '/' + model.id;
                    });

                    // Bind `data` to `callback` to call after
                    // `model.collection` models' ids are persisted.
                    callback = callback ? _.partial(callback, data) : void 0;

                    // Persist `model.collection` models' ids.
                    localforage.setItem(model.collection.sync.localforageKey, collectionData, callback);
                } else if (callback) {
                    callback(data);
                }
            });
        },

        create: function(model, callbacks) {
            // We always have an ID available by this point, so we just call
            // the update method.
            return this.update(model, callbacks);
        },

        update: function(model, callbacks) {
            this.save(model, function(data) {
                if (callbacks.success) {
                    callbacks.success(data);
                }
            });
        },

        find: function(model, callbacks) {
            localforage.getItem(model.sync.localforageKey, function(data) {
                if (!_.isEmpty(data)) {
                    if (callbacks.success) {
                        callbacks.success(data);
                    }
                } else if (callbacks.error) {
                    callbacks.error();
                }
            });
        },

        // Only used by `Backbone.Collection#sync`.
        findAll: function(collection, callbacks) {
            localforage.getItem(collection.sync.localforageKey, function(data) {
                if (data && data.length) {
                    var done = function () {
                        if (callbacks.success) {
                            callbacks.success(data);
                        }
                    };

                    // Only execute `done` after getting all of the
                    // collection's models.
                    done = _.after(data.length, done);

                    var onModel = function(i, model) {
                        data[i] = model;
                        done();
                    };

                    for (var i = 0; i < data.length; ++i) {
                        localforage.getItem(data[i], _.partial(onModel, i));
                    }
                } else {
                    data = [];
                    if (callbacks.success) {
                        callbacks.success(data);
                    }
                }
            });
        },

        destroy: function(model, callbacks) {
            localforage.removeItem(model.sync.localforageKey, function() {
                var json = model.toJSON();
                if (callbacks.success) {
                    callbacks.success(json);
                }
            });
        }
    };

    return Backbone.localforage;
}));