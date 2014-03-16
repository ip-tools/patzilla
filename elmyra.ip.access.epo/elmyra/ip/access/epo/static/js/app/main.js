// -*- coding: utf-8 -*-
// (c) 2013,2014 Andreas Motl, Elmyra UG

/**
 * ------------------------------------------
 *            generic utilities
 * ------------------------------------------
 */

function to_list(value) {
    return _.isArray(value) && value || [value];
}


/**
 * ------------------------------------------
 *            application objects
 * ------------------------------------------
 */
OpsChooserApp = Backbone.Marionette.Application.extend({

    // send to server and process response
    perform_search: function(options) {
        var query = $('#query').val();
        if (!_.isEmpty(query)) {
            var page_size = this.metadata.get('page_size');
            var default_range = '1-' + page_size;
            var range = options && options.range ? options.range : default_range;
            opsChooserApp.search.perform(this.documents, this.metadata, query, range);
        }
    },

    send_query: function(query, options) {
        if (query) {
            $('#query').val(query);
            opsChooserApp.perform_search(options);
            $(window).scrollTop(0);
        }
    }

});
opsChooserApp = new OpsChooserApp();

opsChooserApp.addRegions({
    metadataRegion: "#ops-metadata-region",
    listRegion: "#ops-collection-region",
    paginationRegionTop: "#ops-pagination-region-top",
    paginationRegionBottom: "#ops-pagination-region-bottom",
});


/**
 * ------------------------------------------
 *                view objects
 * ------------------------------------------
 */
OpsExchangeDocumentView = Backbone.Marionette.ItemView.extend({
    //template: "#ops-entry-template",
    template: _.template($('#ops-entry-template').html(), this.model, {variable: 'data'}),
    tagName: 'div',
    className: 'row-fluid',

    events: {
        'click .rank_up img': 'rankUp',
        'click .rank_down img': 'rankDown',
        'click a.disqualify': 'disqualify'
    },

    // actions to run after populating the view
    // e.g. to bind click handlers on individual records
    onDomRefresh: function() {

        var patent_number = this.model.attributes.get_patent_number();
        opsChooserApp.collectionView.basket_update_ui_entry(patent_number);

    },

});

OpsExchangeDocumentCollectionView = Backbone.Marionette.CompositeView.extend({
    tagName: "div",
    id: "opsexchangedocumentcollection",
    className: "container",
    template: "#ops-collection-template",
    itemView: OpsExchangeDocumentView,

    appendHtml: function(collectionView, itemView) {
        $(collectionView.el).append(itemView.el);
    },

    // backpropagate current basket entries into checkbox state
    basket_update_ui_entry: function(entry) {
        //console.log(this.model);
        var payload = $('#basket').val();
        var checkbox_element = $('#' + 'chk-patent-number-' + entry);
        var add_button_element = $('#' + 'add-patent-number-' + entry);
        var remove_button_element = $('#' + 'remove-patent-number-' + entry);
        if (_.string.include(payload, entry)) {
            checkbox_element && checkbox_element.prop('checked', true);
            add_button_element && add_button_element.hide();
            remove_button_element && remove_button_element.show();
        } else {
            checkbox_element && checkbox_element.prop('checked', false);
            add_button_element && add_button_element.show();
            remove_button_element && remove_button_element.hide();
        }
    },

});

PaginationView = Backbone.Marionette.ItemView.extend({
    tagName: "div",
    //id: "paginationview",
    template: "#ops-pagination-template",

    initialize: function() {
        this.listenTo(this.model, "change", this.render);
    },

    onDomRefresh: function() {
    },

});

MetadataView = Backbone.Marionette.ItemView.extend({
    tagName: "div",
    //id: "paginationview",
    template: "#ops-metadata-template",

    initialize: function() {
        this.listenTo(this.model, "change", this.render);
    },

    onDomRefresh: function() {
    },

});




/**
 * ------------------------------------------
 *           bootstrap application
 * ------------------------------------------
 */

// model initializer
opsChooserApp.addInitializer(function(options) {

    // application domain model objects
    this.search = new OpsPublishedDataSearch();
    this.metadata = new OpsExchangeMetadata();
    this.documents = new OpsExchangeDocumentCollection();

    // model for basket component
    this.basketModel = new BasketModel();

});

// view initializer
opsChooserApp.addInitializer(function(options) {

    // bind model objects to view objects
    this.metadataView = new MetadataView({
        model: this.metadata
    });
    this.collectionView = new OpsExchangeDocumentCollectionView({
        collection: this.documents
    });
    this.paginationViewTop = new PaginationView({
        model: this.metadata
    });
    this.paginationViewBottom = new PaginationView({
        model: this.metadata
    });


    var basketView = new BasketView({
        el: $('#basket-area'),
        model: this.basketModel,
    });
    basketView.render();


    // bind view objects to region objects
    opsChooserApp.metadataRegion.show(this.metadataView);
    opsChooserApp.listRegion.show(this.collectionView);
    opsChooserApp.paginationRegionTop.show(this.paginationViewTop);
    opsChooserApp.paginationRegionBottom.show(this.paginationViewBottom);
});

// component connect initializer
opsChooserApp.addInitializer(function(options) {
    this.listenTo(this.basketModel, "change:add", this.collectionView.basket_update_ui_entry);
    this.listenTo(this.basketModel, "change:remove", this.collectionView.basket_update_ui_entry);
});


opsChooserApp.addInitializer(function(options) {
    // automatically run search after bootstrapping application
    this.perform_search();
});

$(document).ready(function() {

    console.log("OpsChooserApp starting");

    // process and propagate application ingress parameters
    //var url = $.url(window.location.href);
    //var query = url.param('query');
    //query = 'applicant=IBM';
    //query = 'publicationnumber=US2013255753A1';

    opsChooserApp.start();

    boot_application();

});
