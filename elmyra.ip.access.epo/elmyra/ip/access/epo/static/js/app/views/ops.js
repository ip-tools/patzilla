// -*- coding: utf-8 -*-
// (c) 2013,2014 Andreas Motl, Elmyra UG

OpsExchangeDocumentView = Backbone.Marionette.Layout.extend({
    //template: "#ops-entry-template",
    template: _.template($('#ops-entry-template').html(), this.model, {variable: 'data'}),
    tagName: 'div',
    className: 'row-fluid',

    regions: {
        region_comment_button: '#region-comment-button',
        region_comment_text: '#region-comment-text',
    },

    initialize: function() {
        console.log('OpsExchangeDocumentView.initialize');
        this.templateHelpers.config = opsChooserApp.config;
    },

    templateHelpers: {
        get_linkmaker: function() {
            return new Ipsuite.LinkMaker(this);
        },
    },

    onDomRefresh: function() {
        console.log('OpsExchangeDocumentView.onDomRefresh');

        // Attach current model reference to result entry dom container so it can be used by different subsystems
        // A reference to the model is required for switching between document details (biblio/fulltext)
        // and for acquiring abstracts from third party data sources.
        var container = $(this.el).find('.ops-collection-entry');
        $(container).prop('ops-document', this.model.attributes);

    },

    events: {
        'click .rank_up img': 'rankUp',
        'click .rank_down img': 'rankDown',
        'click a.disqualify': 'disqualify',
    },

});

OpsExchangeDocumentCollectionView = Backbone.Marionette.CompositeView.extend({
    tagName: "div",
    id: "opsexchangedocumentcollection",
    className: "container",
    template: "#ops-collection-template",
    itemView: OpsExchangeDocumentView,

    initialize: function(options) {
        console.log('OpsExchangeDocumentCollectionView.initialize');
    },

    // Override and disable add:render event, see also:
    // https://github.com/marionettejs/backbone.marionette/issues/640
    _initialEvents: function() {
        if (this.collection) {
            //this.listenTo(this.collection, "add", this.addChildView, this);
            this.listenTo(this.collection, "remove", this.removeItemView, this);
            this.listenTo(this.collection, "reset", this.render, this);
        }
    },

    // override the "close" method, otherwise the events bound by "_initialEvents" would vanish
    // which leads to the view children not being re-rendered when resetting its collection.
    // See also region.show(view, {preventClose: true}) in more recent versions of Marionette.
    close: function() {
    },

    onRender: function() {
        console.log('OpsExchangeDocumentCollectionView.onRender');
    },

    onDomRefresh: function() {
        console.log('OpsExchangeDocumentCollectionView.onDomRefresh');
    },

});

MetadataView = Backbone.Marionette.ItemView.extend({
    tagName: "div",
    //id: "paginationview",
    //template: "#ops-metadata-template",
    template: _.template($('#ops-metadata-template').html(), this.model, {variable: 'data'}),

    initialize: function() {
        this.templateHelpers.config = opsChooserApp.config;
        this.listenTo(this.model, "change", this.render);
        this.listenTo(this, "render", this.setup_ui);
    },

    templateHelpers: {},

    setup_ui: function() {
        log('MetadataView.setup_ui');

        $('.content-chooser > button[data-toggle="tab"]').on('show', function (e) {
            // e.target // activated tab
            // e.relatedTarget // previous tab

            var list_type = $(this).data('list-type');
            if (list_type == 'ops') {
                opsChooserApp.listRegion.show(opsChooserApp.collectionView);

            } else if (list_type == 'upstream') {
                opsChooserApp.listRegion.show(opsChooserApp.resultView);
            }

        });

    },

});


OpsFamilyVerboseMemberView = Backbone.Marionette.ItemView.extend({

    template: _.template($('#ops-family-verbose-member-template').html(), this.model, {variable: 'data'}),
    tagName: 'tr',
    //className: 'row-fluid',
    //style: 'margin-bottom: 10px',

});

OpsFamilyVerboseCollectionView = Backbone.Marionette.CompositeView.extend({

    template: "#ops-family-verbose-collection-template",
    itemView: OpsFamilyVerboseMemberView,

    id: "ops-family-verbose-verbose-collection",
    //tagName: "div",
    //className: "container-fluid",

    appendHtml: function(collectionView, itemView) {
        collectionView.$('tbody').append(itemView.el);
    }

});


OpsFamilyCompactMemberView = Backbone.Marionette.ItemView.extend({

    template: _.template($('#ops-family-compact-member-template').html(), this.model, {variable: 'data'}),
    tagName: 'tr',
    //tagName: 'div',
    //className: 'row-fluid',
    //style: 'margin-bottom: 10px',

});

OpsFamilyCompactCollectionView = Backbone.Marionette.CompositeView.extend({

    template: "#ops-family-compact-collection-template",
    itemView: OpsFamilyCompactMemberView,

    id: "ops-family-compact-collection",
    //tagName: "div",
    //className: "container-fluid",

    appendHtml: function(collectionView, itemView) {
        collectionView.$('tbody').append(itemView.el);
    },

});


OpsFamilyCitationsMemberView = Backbone.Marionette.ItemView.extend({

    template: _.template($('#ops-family-citations-member-template').html(), this.model, {variable: 'data'}),
    tagName: 'tr',

    templateHelpers: {
        get_patent_citation_list: function(enrich) {
            if (this['exchange-document']) {
                var exchange_document = new OpsExchangeDocument(this['exchange-document']);
                var citations = exchange_document.attributes.get_patent_citation_list(enrich);
                return citations;
            } else {
                return [];
            }
        },
        get_citations_environment_button: function() {
            var exchange_document = new OpsExchangeDocument(this['exchange-document']);
            var citations_environment_button = exchange_document.attributes.get_citations_environment_button();
            return citations_environment_button;
        },
    },

});

OpsFamilyCitationsCollectionView = Backbone.Marionette.CompositeView.extend({

    id: "ops-family-citations-collection",
    //template: "#ops-family-citations-collection-template",
    template: _.template($('#ops-family-citations-collection-template').html(), this.collection, {variable: 'data'}),
    itemView: OpsFamilyCitationsMemberView,

    appendHtml: function(collectionView, itemView) {
        collectionView.$('tbody').append(itemView.el);
    },

    // Override and disable add:render event, see also:
    // https://github.com/marionettejs/backbone.marionette/issues/640
    _initialEvents: function() {
        if (this.collection) {
            //this.listenTo(this.collection, "add", this.addChildView, this);
            this.listenTo(this.collection, "remove", this.removeItemView, this);
            this.listenTo(this.collection, "reset", this.render, this);
        }
    },

    templateHelpers: function() {

        // implement interface required for reusing #ops-citations-environment-button-template
        return {

            // If your template needs access to the collection, you'll need to pass it via templateHelpers
            // https://github.com/marionettejs/backbone.marionette/blob/master/docs/marionette.compositeview.md#composite-model-template
            items: this.collection.toJSON(),

            get_citations_environment_button: function() {
                var tpl = _.template($('#ops-citations-environment-button-template').html());
                return tpl({data: this});
            },

            has_citations: function() {
                return this.items.length > 0;
            },
            get_patent_citation_list: function(links, id_type) {
                id_type = id_type || 'docdb';

                // aggregate cited references across all family members
                var citations_set = new Set();
                _.each(this.items, function(item) {
                    var exchange_document = new OpsExchangeDocument(item['exchange-document']);
                    var citations_local = exchange_document.attributes.get_patent_citation_list(false, 'epodoc');
                    _.each(citations_local, function(citation) {
                        citations_set.add(citation);
                    });
                });

                var citations = Array.from(citations_set);
                return citations;

            },

            get_items_query: function(items, fieldname, operator) {
                // FIXME: limit query to 10 items due to ops restriction
                items = items.slice(0, 10);
                items = items.map(function(item) { return fieldname + '=' + item; });
                var query = items.join(' ' + operator + ' ');
                return query;
            },
            get_same_citations_query: function() {
                var items = this.get_patent_citation_list(false, 'epodoc');
                return this.get_items_query(items, 'ct', 'OR');
            },

            get_citing_query: function() {
                throw Error('not implemented');
            },
            get_publication_number: function(kind) {
                throw Error('not implemented');
            },

        };

    },

    get_highlight_styles: function() {
        var styles = _.range(0, 360, 35).map(function(hue) {
            var style = {
                backgroundColor: _.template('hsla(  <%= hue %>, 100%, 88%, 1)')({hue: hue}),
            };
            return style;
        });
        return styles;
    },

    highlight: function() {

        // count all cited references
        var citations = {};
        _.each(this.collection.models, function(model) {
            var exchange_document = model.attributes['exchange-document'];
            if (exchange_document && exchange_document['bibliographic-data']) {
                var citation_list = model.attributes.get_patent_citation_list(exchange_document['bibliographic-data'], false, 'epodoc');
                _.each(citation_list, function(citation_item) {
                    if (!citations[citation_item]) {
                        citations[citation_item] = 0;
                    }
                    citations[citation_item]++;
                });
            }
        });

        // reject citation references occurring only once
        /*
         // FIXME: use "pick" of more recent underscore release (1.6.0), this can do objects
         citations = _.pick(citations, function(value, key, object) {
         return value > 1;
         });
         */
        _.each(citations, function(value, key) {
            if (value < 2) {
                delete citations[key];
            }
        });


        // highlight citations
        var style_queue;
        var _this = this;
        _.each(citations, function(index, citation) {
            if (!citation) { return; }

            // refill style queue
            if (_.isEmpty(style_queue)) {
                style_queue = _this.get_highlight_styles();
            }

            // get next style available
            var style = style_queue.shift();

            var class_name = _.uniqueId('citation-highlight-');

            // perform highlighting
            _this.$el.highlight(citation, {className: 'highlight-base ' + class_name, wholeWords: true, minLength: 3});

            // apply style
            $('.' + class_name).css(style);

        });

    },

    setup_ui: function() {
        // bind user notification to all same citations links of "explore citation environment" fame
        this.$el.find('.same-citations-link').unbind('click');
        this.$el.find('.same-citations-link').on('click', function(event) {
            var citations_length = $(this).data('length');
            if (citations_length > 10) {
                event.preventDefault();
                event.stopPropagation();
                opsChooserApp.ui.notify(
                    'Querying the same citations is capped to the first 10 cited references. Sorry for this limitation.',
                    {type: 'warning', icon: 'icon-cut'});
                var _this = this;
                setTimeout(function() {
                    open($(_this).attr("href"));
                }, 3000);
            }
        });
    },

    onDomRefresh: function() {
        this.setup_ui();
        this.highlight();
    },

});
