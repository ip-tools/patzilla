// -*- coding: utf-8 -*-
// (c) 2014,2015 Andreas Motl, Elmyra UG

KeywordMapModel = Backbone.RelationalModel.extend({

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

KeywordMapCollection = Backbone.Collection.extend({
    sync: Backbone.localforage.sync('KeywordMap'),
    find: Backbone.localforage.find,
    model: KeywordMapModel,

    // initialize model
    initialize: function() {
        console.log('KeywordMapCollection.initialize');
    },

});


KeywordEditorEntryView = Backbone.Marionette.ItemView.extend({

    tagName: "tr",
    template: '#keyword-editor-entry-template',

    initialize: function() {
        //console.log('KeywordEditorEntryView.initialize');
    },

    templateHelpers: {
    },

    onDomRefresh: function() {
        //console.log('KeywordEditorEntryView.onDomRefresh');
    },

    events: {
    },

});

KeywordEditorView = Backbone.Marionette.CompositeView.extend({

    tagName: "div",
    id: "keyword-editor",
    className: "modal",
    template: "#keyword-editor-template",
    itemView: KeywordEditorEntryView,

    appendHtml: function(collectionView, itemView) {
        collectionView.$('tbody').append(itemView.el);
    },

    initialize: function() {
        console.log('KeywordEditorView.initialize');
    },

    setup_ui: function() {
        this.collection.fetch({success: function(response) {

            _.each(response.models, function(model) {
                var class_name = 'highlight-strong-' + model.get('name');
                var style = model.get('style');
                style = _(style).extend(opsChooserApp.keywords.styles_strong);

                // apply style
                $('.' + class_name).css(style);

            });
        }});
    },

    templateHelpers: {
    },

    onShow: function() {

        this.setup_ui();

        var _this = this;

        // "save" button should save all models and close modal dialog
        $('#keyword-editor-save-button').unbind('click');
        $('#keyword-editor-save-button').click(function() {
            $.when(_this.save_models()).then(function() {
                opsChooserApp.keywords.keyword_modal.close();
                opsChooserApp.keywords.highlight_from_user();
            });
        });
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


KeywordsController = Marionette.Controller.extend({

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
        //borderBottom: '1px dashed black',
        borderLeft: '1px dotted black',
    },

    initialize: function(options) {
        console.log('KeywordsController.initialize');
        this.keywordmaps = new KeywordMapCollection();
        this.setup_fixtures();
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

        this.keyword_editor = new KeywordEditorView({collection: this.keywordmaps});

        var _this = this;

        $('#highlighting-map-edit-action').unbind('click');
        $('#highlighting-map-edit-action').click(function() {
            _this.keyword_modal = new ModalRegion({el: '#keyword-editor-modal'});
            _this.keyword_modal.show(_this.keyword_editor);
        });

    },

    highlight: function(element) {
        this.highlight_from_query(element);
        this.highlight_from_user(element);
    },

    highlight_from_query: function(element) {

        var highlight_selector = element;
        if (!highlight_selector) { highlight_selector = '.keyword'; }

        var style_queue = ['yellow', 'green', 'orange', 'turquoise', 'blue', 'violet', 'magenta'];
        var style_queue_work;
        var _this = this;
        _.each(opsChooserApp.metadata.get('keywords'), function(keyword) {
            log('keyword:', keyword);
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
                $(highlight_selector).highlight(keyword, {className: 'highlight-base ' + class_name, wholeWords: true, minLength: 3});

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
                    $(highlight_selector).highlight(keyword, {className: 'highlight-base ' + class_name, wholeWords: true, minLength: 3});
                });
                style = _(style).extend(_this.styles_strong);
                $('.' + class_name).css(style);
            });
        }});

    },

});


// setup plugin
opsChooserApp.addInitializer(function(options) {
    this.keywords = new KeywordsController();
    this.listenTo(this, 'results:ready', function() {
        this.keywords.setup_ui();
        this.keywords.highlight();
    });
});
