// -*- coding: utf-8 -*-

function to_list(value) {
    return _.isArray(value) && value || [value];
}


OpsChooserApp = new Backbone.Marionette.Application();

OpsChooserApp.addRegions({
    listRegion: "#ops-collection-region",
    paginationRegion: "#ops-pagination-region",
});

OpsPublishedDataSearch = Backbone.Model.extend({
    url: '/api/ops/published-data/search',
    perform: function(documents, query, range) {

        $('#spinner').show();

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

                var entries;
                if (search_result) {
                    // unwrap and create model object of each record
                    var exchange_documents = to_list(search_result['exchange-documents']);
                    entries = _.map(exchange_documents, function(entry) { return new OpsExchangeDocument(entry['exchange-document']); });
                }

                // propagate data to model collection instance
                documents.reset(entries);

            },
        });

    },
});

function parties_to_list(container, value_attribute_name) {
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

    // TODO: somehow display in gui which one is the epodoc and which one is the original value
    var entries = [];
    _.each(_.range(1, parseInt(sequence_max) + 1), function(sequence) {
        sequence = sequence.toString();
        var epodoc_value = groups['epodoc'][sequence];
        var original_value = groups['original'][sequence];
        entries.push(epodoc_value + ' / ' + original_value);
    });

    return entries;
}


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
            var applicants_node = this['bibliographic-data']['parties']['applicants']['applicant'];
            return parties_to_list(applicants_node, 'applicant-name');
        },

        get_inventors: function() {
            var inventors_node = this['bibliographic-data']['parties']['inventors']['inventor'];
            return parties_to_list(inventors_node, 'inventor-name');
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


// FIXME: why does underscore.string's "include" not work?
function contains(string, pattern) {
    return string.indexOf(pattern) > -1;
}

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
        var patent_number = this.model.attributes.get_patent_number();
        if (contains(payload, patent_number)) {
            var checkbox_id = 'patent-number-' + patent_number;
            $('#' + checkbox_id).prop('checked', true);
        }

        // handle checkbox clicks by add-/remove-operations on basket
        $(".patent-number").click(function() {
            var payload = $('#basket').val();
            var patent_number = this.value;
            // FIXME: why does underscore.string's "include" not work?
            if (this.checked && !contains(payload, patent_number))
                payload += patent_number + '\n';
            if (!this.checked && contains(payload, patent_number))
                payload = payload.replace(patent_number + '\n', '');
            $('#basket').val(payload);
        });

        // use jquery.shorten on abstract text
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

PaginationView = Backbone.Marionette.CompositeView.extend({
    tagName: "div",
    //id: "opsexchangedocumentcollection",
    id: "pv",
    //className: "table table-bordered table-condensed table-hover",
    template: "#ops-pagination-template",
    //itemView: OpsExchangeDocumentView,

    appendHtml2: function(collectionView, itemView) {
        collectionView.$("tbody#ops-collection-tbody").append(itemView.el);
    },
});

OpsChooserApp.addInitializer(function(options) {
    var collectionView = new OpsExchangeDocumentCollectionView({
        collection: options.documents
    });
    var paginationView = new PaginationView({
        //collection: options.documents
    });

    OpsChooserApp.listRegion.show(collectionView);
    OpsChooserApp.paginationRegion.show(paginationView);

    $('div.pagination a').click(function() {
        var action = $(this).attr('action');
        var range = $(this).attr('range');
        //return;

        var querystring = $('#query').val();
        if (!_.isEmpty(querystring) && range) {
            OpsChooserApp.search.perform(OpsChooserApp.documents, querystring, range);
        }

        return false;
    });

});

$(document).ready(function() {

    console.log("OpsChooserApp starting");

    // process and propagate application ingress parameters
    var url = $.url(window.location.href);
    var query = url.param('query');
    //query = 'applicant=IBM';
    //query = 'publicationnumber=US2013255753A1';

    // create application domain objects
    OpsChooserApp.search = new OpsPublishedDataSearch();
    OpsChooserApp.documents = new OpsExchangeDocumentCollection();

    // automatically run query if submitted
    if (!_.isEmpty(query))
        OpsChooserApp.search.perform(OpsChooserApp.documents, query);

    OpsChooserApp.start({documents: OpsChooserApp.documents});

});

$('input#query-button').click(function() {
    var querystring = $('textarea#query').val();
    //send to server and process response
    //alert(querystring);
    if (!_.isEmpty(querystring)) {
        OpsChooserApp.search.perform(OpsChooserApp.documents, querystring);
    }
});
