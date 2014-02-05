// -*- coding: utf-8 -*-

/**
 * ------------------------------------------
 *            generic utilities
 * ------------------------------------------
 */

function to_list(value) {
    return _.isArray(value) && value || [value];
}

// FIXME: why does underscore.string's "include" not work?
function contains(string, pattern) {
    if (!string) return false;
    return string.indexOf(pattern) > -1;
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
            if (options && options.range) {
                opsChooserApp.search.perform(this.documents, this.metadata, query, options.range);
            } else {
                opsChooserApp.search.perform(this.documents, this.metadata, query);
            }
        }
    }
});
opsChooserApp = new OpsChooserApp();

opsChooserApp.addRegions({
    listRegion: "#ops-collection-region",
    paginationRegion: "#ops-pagination-region",
});



/**
 * ------------------------------------------
 *               model objects
 * ------------------------------------------
 */
OpsPublishedDataSearch = Backbone.Model.extend({
    url: '/api/ops/published-data/search',
    perform: function(documents, metadata, query, range) {

        $('#spinner').show();
        var self = this;

        this.fetch({
            data: $.param({ query: query, range: range}),
            success: function (payload) {

                $('#spinner').hide();

                //console.log("payload raw:");
                //console.log(payload);
                console.log("payload data:");
                console.log(payload['attributes']);

                // get "node" containing record list from nested json response
                var search_result = payload['attributes']['ops:world-patent-data']['ops:biblio-search']['ops:search-result'];

                // unwrap response by creating a list of model objects from records
                var entries;
                if (search_result) {
                    var exchange_documents = to_list(search_result['exchange-documents']);
                    entries = _.map(exchange_documents, function(entry) { return new OpsExchangeDocument(entry['exchange-document']); });
                }

                // propagate data to model collection instance
                documents.reset(entries);

                // propagate metadata to model
                var total_result_count = payload['attributes']['ops:world-patent-data']['ops:biblio-search']['@total-result-count'];
                metadata.set({result_count: total_result_count});

                // HACK: by now, run action bindings here after rendering data entries
                listview_bind_actions();

            },
        });

    },
});

OpsExchangeMetadata = Backbone.Model.extend({

    defaults: {
        result_count: null,
    }

});

OpsExchangeDocument = Backbone.Model.extend({

    defaults: {
        selected: false,

        // TODO: move these methods to "viewHelpers"
        // http://lostechies.com/derickbailey/2012/04/26/view-helpers-for-underscore-templates/
        // https://github.com/marionettejs/backbone.marionette/wiki/View-helpers-for-underscore-templates#using-this-with-backbonemarionette

        get_patent_number: function() {
            return this['@country'] + this['@doc-number'] + this['@kind'];
        },

        get_applicants: function() {
            var applicants_root_node = this['bibliographic-data']['parties']['applicants'];
            applicants_root_node = applicants_root_node || [];
            var applicants_node = applicants_root_node['applicant'];
            return this.parties_to_list(applicants_node, 'applicant-name');
        },

        get_inventors: function() {
            var inventors_root_node = this['bibliographic-data']['parties']['inventors'];
            inventors_root_node = inventors_root_node || [];
            var inventors_node = inventors_root_node['inventor'];
            return this.parties_to_list(inventors_node, 'inventor-name');
        },

        parties_to_list: function(container, value_attribute_name) {

            // deserialize list of parties (applicants/inventors) from exchange payload
            var sequence_max = "0";
            var groups = {};
            _.each(container, function(item) {
                var data_format = item['@data-format'];
                var sequence = item['@sequence'];
                var value = _.string.trim(item[value_attribute_name]['name']['$'], ', ');
                groups[data_format] = groups[data_format] || {};
                groups[data_format][sequence] = value;
                if (sequence > sequence_max)
                    sequence_max = sequence;
            });
            //console.log(groups);

            // TODO: somehow display in gui which one is the "epodoc" and which one is the "original" value
            var entries = [];
            _.each(_.range(1, parseInt(sequence_max) + 1), function(sequence) {
                sequence = sequence.toString();
                var epodoc_value = groups['epodoc'][sequence];
                var original_value = groups['original'][sequence];
                entries.push(epodoc_value + ' / ' + original_value);
            });

            return entries;

        },

        get_drawing_url: function() {
            // http://ops.epo.org/3.1/rest-services/published-data/images/EP/1000000/PA/firstpage.png?Range=1
            // http://ops.epo.org/3.1/rest-services/published-data/images/US/20130311929/A1/thumbnail.tiff?Range=1
            var url_tpl = _.template('/api/ops/<%= country %><%= docnumber %>.<%= kind %>/image/drawing');
            var url = url_tpl({country: this['@country'], docnumber: this['@doc-number'], kind: this['@kind']});
            return url;
        },

        get_fullimage_url: function() {
            // http://ops.epo.org/3.1/rest-services/published-data/images/EP/1000000/A1/fullimage.pdf?Range=1
            var url_tpl = _.template('/api/ops/<%= country %><%= docnumber %>.<%= kind %>/image/full');
            var url = url_tpl({country: this['@country'], docnumber: this['@doc-number'], kind: this['@kind']});
            return url;
        },

    },

    select: function() {
        this.set('selected', true);
    },
    unselect: function() {
        this.set('selected', false);
    },


});

OpsExchangeDocumentCollection = Backbone.Collection.extend({

    model: OpsExchangeDocument,

    initialize: function(collection) {
        var self = this;
    },

});



/**
 * ------------------------------------------
 *                view objects
 * ------------------------------------------
 */
OpsExchangeDocumentView = Backbone.Marionette.ItemView.extend({
    //template: "#ops-entry-template",
    template: _.template($('#ops-entry-template').html(), this.model, {variable: 'data'}),
    tagName: 'tr',
    className: 'entry',

    events: {
        'click .rank_up img': 'rankUp',
        'click .rank_down img': 'rankDown',
        'click a.disqualify': 'disqualify'
    },

    // actions to run after populating the view
    // e.g. to bind click handlers on individual records
    onDomRefresh: function () {

        // backpropagate current basket entries into checkbox state
        //console.log(this.model);
        var payload = $('#basket').val();
        if (payload) {
            var patent_number = this.model.attributes.get_patent_number();
            if (contains(payload, patent_number)) {
                var checkbox_id = 'chk-patent-number-' + patent_number;
                $('#' + checkbox_id).prop('checked', true);
            }
        }

        // handle checkbox clicks by add-/remove-operations on basket
        $(".chk-patent-number").click(function() {
            var payload = $('#basket').val();
            var patent_number = this.value;
            //console.log(patent_number);
            // FIXME: why does underscore.string's "include" not work?
            if (this.checked && !contains(payload, patent_number))
                payload += patent_number + '\n';
            if (!this.checked && contains(payload, patent_number))
                payload = payload.replace(patent_number + '\n', '');
            $('#basket').val(payload);
        });

        // use jquery.shorten on "abstract" text
        $(".abstract").shorten({showChars: 200, moreText: 'mehr', lessText: 'weniger'});

    },

});

OpsExchangeDocumentCollectionView = Backbone.Marionette.CompositeView.extend({
    tagName: "table",
    id: "opsexchangedocumentcollection",
    className: "table table-bordered table-condensed table-hover",
    template: "#ops-collection-template",
    itemView: OpsExchangeDocumentView,

    appendHtml: function(collectionView, itemView) {
        collectionView.$("tbody#ops-collection-tbody").append(itemView.el);
    },

});

PaginationView = Backbone.Marionette.ItemView.extend({
    tagName: "div",
    id: "paginationview",
    template: "#ops-pagination-template",

    initialize: function() {
        console.log('PaginationView.initialize');
        this.listenTo(this.model, "change", this.render);
    },

    onDomRefresh: function() {
        console.log('PaginationView.onDomRefresh');
        $('div.pagination a').click(function() {
            var action = $(this).attr('action');
            var range = $(this).attr('range');
            opsChooserApp.perform_search({range: range});
            return false;
        });
    },

});

function pdf_display(element_id, url, page) {
    // embed pdf object
    var pdf_object = new PDFObject({
        url: url + '?page=' + page,
        id: 'myPDF',
        pdfOpenParams: {
            navpanes: 0,
            toolbar: 0,
            statusbar: 0,
            view: 'FitB',
            //zoom: '100',
        },
    });
    pdf_object.embed(element_id);
}

function pdf_set_headline(document_number, page) {
    var headline = document_number + ' Page ' + page;
    $(".modal-header #ops-pdf-modal-label").empty().append(headline);
}

function listview_bind_actions() {

    // pdf action button
    $(".pdf-open").click(function() {

        var patent_number = $(this).data('patent-number');
        var pdf_url = $(this).data('pdf-url');
        var pdf_page = 1;

        pdf_set_headline(patent_number, pdf_page);
        pdf_display('pdf', pdf_url, pdf_page);

        // pdf paging actions
        $("#pdf-previous").unbind();
        $("#pdf-previous").click(function() {
            if (pdf_page == 1) return;
            pdf_page -= 1;
            pdf_set_headline(patent_number, pdf_page);
            pdf_display('pdf', pdf_url, pdf_page);
        });
        $("#pdf-next").unbind();
        $("#pdf-next").click(function() {
            pdf_page += 1;
            pdf_set_headline(patent_number, pdf_page);
            pdf_display('pdf', pdf_url, pdf_page);
        });

    });

}


/**
 * ------------------------------------------
 *           bootstrap application
 * ------------------------------------------
 */

opsChooserApp.addInitializer(function(options) {
    // create application domain model objects
    this.search = new OpsPublishedDataSearch();
    this.metadata = new OpsExchangeMetadata();
    this.documents = new OpsExchangeDocumentCollection();
});

opsChooserApp.addInitializer(function(options) {

    // bind model objects to view objects
    var collectionView = new OpsExchangeDocumentCollectionView({
        collection: this.documents
    });
    var paginationView = new PaginationView({
        model: this.metadata
    });

    // bind view objects to region objects
    opsChooserApp.listRegion.show(collectionView);
    opsChooserApp.paginationRegion.show(paginationView);
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

    $('input#query-button').click(function() {
        opsChooserApp.perform_search();
    });

});
