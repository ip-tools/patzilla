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
        enrich_links: function() {
            return opsChooserApp.document_base.enrich_links.apply(this, arguments);
        },
        enrich_link: function() {
            return opsChooserApp.document_base.enrich_link.apply(this, arguments);
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


OpsFamilyMemberVerboseView = Backbone.Marionette.ItemView.extend({

    template: _.template($('#ops-family-verbose-member-template').html(), this.model, {variable: 'data'}),
    tagName: 'tr',
    //className: 'row-fluid',
    //style: 'margin-bottom: 10px',

    templateHelpers: {
        enrich_link: function() {
            return opsChooserApp.document_base.enrich_link.apply(this, arguments);
        },
    },

});

OpsFamilyVerboseCollectionView = Backbone.Marionette.CompositeView.extend({

    template: "#ops-family-verbose-collection-template",
    itemView: OpsFamilyMemberVerboseView,

    id: "ops-family-verbose-verbose-collection",
    //tagName: "div",
    //className: "container-fluid",

    appendHtml: function(collectionView, itemView) {
        collectionView.$('tbody').append(itemView.el);
    }

});


OpsFamilyMemberCompactView = Backbone.Marionette.ItemView.extend({

    template: _.template($('#ops-family-compact-member-template').html(), this.model, {variable: 'data'}),
    tagName: 'tr',
    //tagName: 'div',
    //className: 'row-fluid',
    //style: 'margin-bottom: 10px',

    templateHelpers: {
        enrich_link: function() {
            return opsChooserApp.document_base.enrich_link.apply(this, arguments);
        },
    },

});

OpsFamilyCompactCollectionView = Backbone.Marionette.CompositeView.extend({

    template: "#ops-family-compact-collection-template",
    itemView: OpsFamilyMemberCompactView,

    id: "ops-family-compact-collection",
    //tagName: "div",
    //className: "container-fluid",

    appendHtml: function(collectionView, itemView) {
        collectionView.$('tbody').append(itemView.el);
    }

});
