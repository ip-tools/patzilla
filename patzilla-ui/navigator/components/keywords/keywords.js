// -*- coding: utf-8 -*-
// (c) 2014-2019 Andreas Motl <andreas.motl@ip-tools.org>
'use strict';

import {View, Region, CollectionView} from 'marionette';
import {MarionetteController} from "patzilla.lib.marionette";

require('jquery.highlight.bartaz');

const KeywordMapModel = Backbone.RelationalModel.extend({

    sync: Backbone.localforage.sync('KeywordMap'),
    //collection: ProjectCollection,

    defaults: {
        name: null,
        keywords: [],
        style: null,
    },

    // initialize model
    initialize: function() {
        console.log('KeywordMapModel.initialize');
        // backbone-relational backward-compat
        if (!this.fetchRelated) this.fetchRelated = this.getAsync;
    },

});

const KeywordMapCollection = Backbone.Collection.extend({
    sync: Backbone.localforage.sync('KeywordMap'),
    find: Backbone.localforage.find,
    model: KeywordMapModel,

    // initialize model
    initialize: function() {
        console.log('KeywordMapCollection.initialize');
    },

});


const KeywordEditorEntryView = View.extend({

    tagName: "tr",
    template: require('./keyword-editor-item.html'),

    initialize: function() {
        //console.log('KeywordEditorEntryView.initialize');
    },

    templateContext: {
    },

    onDomRefresh: function() {
        //console.log('KeywordEditorEntryView.onDomRefresh');
    },

    events: {
    },

});

const KeywordEditorView = CollectionView.extend({

    tagName: "div",
    id: "keyword-editor",
    // Close synchronously so Bootstrap cleans up before Marionette removes the view.
    className: "modal",
    template: require('./keyword-editor.html'),
    childView: KeywordEditorEntryView,
    childViewContainer: 'tbody',

    initialize: function() {
        console.log('KeywordEditorView.initialize');
    },

    setup_ui: function() {
        this.collection.fetch({success: function(response) {

            _.each(response.models, function(model) {
                var class_name = 'highlight-strong-' + model.get('name');
                var style = model.get('style');
                style = _(style).extend(navigatorApp.keywords.styles_strong);

                // apply style
                $('.' + class_name).css(style);

            });
        }});
    },

    templateContext: {
    },

    onAttach: function() {
        var view = this;
        var alive = true;
        var shown = false;

        this.once('destroy', function() {
            alive = false;
        });

        $(this.el).one('shown.bs.modal', function() {
            shown = true;
        });

        $(this.el).one('hidden.bs.modal', function() {
            view.destroy();
        });

        this.setup_ui();

        $('#keyword-editor-save-button').one('click', function() {
            $.when(view.save_models()).then(function() {
                if (!alive) {
                    return;
                }

                // Bootstrap ignores hide calls during the opening transition.
                if (shown) {
                    $(view.el).modal('hide');
                } else {
                    $(view.el).one('shown.bs.modal', function() {
                        $(view.el).modal('hide');
                    });
                }

                navigatorApp.keywords.unhighlight();
                navigatorApp.keywords.highlight();
            });
        });

        $(this.el).modal('show');
    },

    onBeforeDestroy: function() {
        $(this.el).off('.keywordEditor');
    },

    save_models: function() {
        var deferred = $.Deferred();
        var _this = this;
        this.collection.fetch({success: function(response) {

            _.each(response.models, function(model) {

                // get keywords from user interface
                var name = model.get('name');
                var container = $('textarea[data-name="' + name + '"]');
                var value = container.val();
                if (value == undefined) { return; }

                // parse keywords
                var keywords = _.map(value.split(','), function(item) {
                    return item.trim();
                });

                // find proper keyword map data model, modify and save
                var records = _this.collection.where({name: name});
                if (!records) { return; }
                var map = records[0];
                map.set('keywords', keywords);
                map.save();

            });

            deferred.resolve();

        }});

        return deferred;
    },

    events: {
    },

});


const KeywordsController = MarionetteController.extend({

    initialize: function(options) {
        console.log('KeywordsController.initialize');
        this.keywordmaps = new KeywordMapCollection();
        this.setup_fixtures();
        this.module_name = 'keywords-user';
        this.module_available = navigatorApp.user_has_module(this.module_name);
    },

    // http://hslpicker.com/
    colors_light: {
        yellow:     {backgroundColor: 'hsla( 60, 100%, 88%, 1)'},
        green:      {backgroundColor: 'hsla(118, 100%, 88%, 1)'},
        orange:     {backgroundColor: 'hsla( 16, 100%, 88%, 1)'},
        turquoise:  {backgroundColor: 'hsla(174, 100%, 88%, 1)'},
        blue:       {backgroundColor: 'hsla(195, 100%, 88%, 1)'},
        violet:     {backgroundColor: 'hsla(247, 100%, 88%, 1)'},
        magenta:    {backgroundColor: 'hsla(315, 100%, 88%, 1)'},
    },

    colors_strong: {
        yellow:     {backgroundColor: 'hsla( 60, 100%, 80%, 1)'},
        green:      {backgroundColor: 'hsla(118, 100%, 80%, 1)'},
        orange:     {backgroundColor: 'hsla( 16, 100%, 80%, 1)'},
        turquoise:  {backgroundColor: 'hsla(174, 100%, 80%, 1)'},
        blue:       {backgroundColor: 'hsla(195, 100%, 80%, 1)'},
        violet:     {backgroundColor: 'hsla(247, 100%, 80%, 1)'},
        magenta:    {backgroundColor: 'hsla(315, 100%, 80%, 1)'},
    },

    styles_strong: {
        /*
        textDecoration: 'underline',
        textDecorationLine: 'underline',
        textDecorationStyle: 'dotted',
        textDecorationColor: '#222222',
        */
        borderBottom: '1px dashed #333333',
        //borderLeft: '1px dotted #333333',
    },

    setup_fixtures: function() {
        var _this = this;
        this.keywordmaps.fetch({success: function(response) {
            if (response.length < _(_this.colors_strong).keys().length) {
                _.each(_(_this.colors_strong).keys(), function(style_name) {
                    var style = _this.colors_strong[style_name];
                    var keywordmap = new KeywordMapModel({
                        name: style_name,
                        style: style,
                    });
                    keywordmap.save();
                    _this.keywordmaps.add(keywordmap);
                });
            }
        }});

    },

    setup_ui: function() {

        var _this = this;

        $('.action-keyword-editor').off('click').on('click', function(event) {
            event.preventDefault();
            if (_this.module_available) {

                // Do not replace an editor while its modal is open or closing.
                if (_this.keyword_editor) {
                    return;
                }

                var editor = new KeywordEditorView({collection: _this.keywordmaps});
                _this.keyword_editor = editor;

                editor.once('destroy', function() {
                    if (_this.keyword_editor === editor) {
                        _this.keyword_editor = null;
                    }
                });

                _this.keyword_modal = new Region({el: '#modal-area'});
                _this.keyword_modal.show(editor);
            } else {
                navigatorApp.ui.notify_module_locked(_this.module_name);
            }
        });

    },

    highlight: function(element) {
        this.highlight_from_query(element);
        this.highlight_from_user(element);
    },

    unhighlight: function(element) {
        var highlight_selector = element;
        if (!highlight_selector) { highlight_selector = '.keyword'; }
        $(highlight_selector).unhighlight({className: 'highlight-base'});
    },

    highlight_from_query: function(element) {

        var highlight_selector = element;
        if (!highlight_selector) { highlight_selector = '.keyword'; }

        var style_queue = _(this.colors_light).keys();
        var style_queue_work;
        var _this = this;
        var keywords = navigatorApp.metadata.get('keywords');
        log('metadata.keywords:', keywords);
        _.each(keywords, function(keyword) {
            if (keyword) {

                // refill style queue
                if (_.isEmpty(style_queue_work)) {
                    style_queue_work = style_queue.slice(0);
                }

                // get next style available
                var style_name = style_queue_work.shift();
                var style = _this.colors_light[style_name];

                var class_name = 'keyword-light-' + style_name;

                // perform highlighting
                $(highlight_selector).highlight(keyword, {className: 'highlight-base ' + class_name, wholeWords: false, minLength: 3});

                // apply style
                $('.' + class_name).css(style);
            }
        });
    },

    highlight_from_user: function(element) {

        var highlight_selector = element;
        if (!highlight_selector) { highlight_selector = '.keyword'; }

        var _this = this;
        this.keywordmaps.fetch({success: function(response) {
            _.each(response.models, function(model) {
                var class_name = 'keyword-strong-' + model.get('name');
                var style = model.get('style');
                var keywords = model.get('keywords');
                _.each(keywords, function(keyword) {
                    if (!keyword) { return; }
                    $(highlight_selector).highlight(keyword, {className: 'highlight-base ' + class_name, wholeWords: false, minLength: 0});
                });
                style = _(style).extend(_this.styles_strong);
                $('.' + class_name).css(style);
            });
        }});

    },

});


// setup plugin
navigatorApp.on("before:start", function(options) {
    this.keywords = new KeywordsController();
    this.listenTo(this, 'application:ready', function() {
        this.keywords.setup_ui();
    });
    this.listenTo(this, 'results:ready', function() {
        this.keywords.setup_ui();
        this.keywords.highlight();
    });
    this.register_component('keywords');
});
