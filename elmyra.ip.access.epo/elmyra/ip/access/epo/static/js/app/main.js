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

    get_datasource: function() {
        var datasource = $('#datasource > .btn.active').data('value');
        return datasource;
    },

    // send to server and process response
    perform_search: function(options) {
        var query = $('#query').val();
        var datasource = this.get_datasource();
        if (!_.isEmpty(query)) {

            if (datasource == 'ops') {
                console.log('ops search: ' + query);
                var range = this.compute_range(options);
                opsChooserApp.search.perform(this.documents, this.metadata, query, range).done(function() {
                    // run action bindings here after rendering data entries
                    listview_bind_actions();
                });

            } else if (datasource == 'depatisnet') {
                console.log('depatisnet search: ' + query);
                var depatisnet = new DepatisnetSearch();
                var self = this;
                depatisnet.perform(query).done(function(response) {

                    //reset_content();
                    reset_content({keep_pager: true});

                    var publication_numbers = response['data'];

                    if (response['message']) {
                        // TODO: refactor to "mkerror" or similar
                        var tpl = _.template($('#alert-template').html());
                        var error = {
                            'title': 'WARNING',
                            'description': response['message'],
                            'clazz': 'alert-warning',
                        };
                        var alert_html = tpl(error);
                        $('#info-area').append(alert_html);
                    }


                    self.metadata.set('keywords', depatisnet.keywords);

                    // compute slice values
                    var range = options && options.range ? options.range : '1-10';
                    //console.log('range:', range);
                    var range_parts = range.split('-');
                    var sstart = parseInt(range_parts[0]);
                    var ssend = parseInt(range_parts[1]) + 1;
                    //console.log('range:', sstart, ssend);

                    if (publication_numbers && sstart > publication_numbers.length) {
                        var msg = 'DEPATISnet: No results for range "' + range + '"';
                        console.warn(msg);

                        // TODO: refactor to "mkerror" or similar
                        var tpl = _.template($('#cornice-error-template').html());
                        var error = {'name': 'query', 'location': 'depatisnet-search', 'description': msg};
                        var alert_html = tpl(error);
                        $('#alert-area').append(alert_html);

                        return;
                    }

                    var query_ops = _(_.map(publication_numbers, function(item) { return 'pn=' + item})).slice(sstart, ssend).join(' OR ');
                    console.log('DEPATISnet: OPS CQL query:', query_ops);


                    // querying by single document numbers has a limit of 10 at OPS
                    self.metadata.set('page_size', 10);


                    //var range = self.compute_range(options);
                    opsChooserApp.search.perform(self.documents, self.metadata, query_ops, '1-10').done(function() {

                        // make the pager display the original query
                        self.metadata.set('query_real', query);

                        // amend the current result range and paging parameter
                        self.metadata.set('result_range', range);
                        self.metadata.set('pagination_entry_count', 17);
                        $('.pagination').removeClass('span10');
                        $('.pagination').addClass('span12');

                        // run action bindings here after rendering data entries
                        listview_bind_actions();

                        // TODO: selecting page size with DEPATISnet is currently not possible
                        $('.page-size-chooser').parent().remove();

                    });

                });
            }

        }
    },

    send_query: function(query, options) {
        if (query) {
            $('#query').val(query);
            opsChooserApp.perform_search(options);
            $(window).scrollTop(0);
        }
    },

    compute_range: function(options) {
        var page_size = this.metadata.get('page_size');
        var default_range = '1-' + page_size;
        var range = options && options.range ? options.range : default_range;
        return range;
    },

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


$(document).ready(function() {

    console.log("OpsChooserApp starting");

    // process and propagate application ingress parameters
    //var url = $.url(window.location.href);
    //var query = url.param('query');
    //query = 'applicant=IBM';
    //query = 'publicationnumber=US2013255753A1';

    opsChooserApp.start();

    boot_application();

    // automatically run search after bootstrapping application
    opsChooserApp.perform_search();

});
