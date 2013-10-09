// -*- coding: utf-8 -*-

OpsChooserApp = new Backbone.Marionette.Application();

OpsChooserApp.addRegions({
    listRegion: "#ops-collection-region"
});

OpsPublishedDataSearch = Backbone.Model.extend({
    url: '/api/ops/published-data/search',
    perform: function(query, documents) {

        this.fetch({
            data: $.param({ query: query}),
            success: function (payload) {
                //console.log("payload raw:");
                //console.log(payload);
                console.log("payload data:");
                console.log(payload['attributes']);

                // get "node" containing record list from nested json response
                var exchange_documents = payload['attributes']['ops:world-patent-data']['ops:biblio-search']['ops:search-result']['exchange-documents'];
                if (!_.isArray(exchange_documents)) {
                    exchange_documents = [exchange_documents];
                }

                // unwrap and create model object of each record
                var entries = _.map(exchange_documents, function(entry) { return new OpsExchangeDocument(entry['exchange-document']); });

                // propagate data to model collection instance
                documents.reset(entries);
            },
        });

    },
});

OpsExchangeDocument = Backbone.Model.extend({

    defaults: {
        selected: false,

        // TODO: move to "viewHelpers"
        // http://lostechies.com/derickbailey/2012/04/26/view-helpers-for-underscore-templates/
        // https://github.com/marionettejs/backbone.marionette/wiki/View-helpers-for-underscore-templates#using-this-with-backbonemarionette
        get_applicants: function() {
            var sequence_max = "0";
            var applicant_groups = {};
            var applicants_node = this['bibliographic-data']['parties']['applicants']['applicant'];
            _.each(applicants_node, function(applicant_node) {
                var data_format = applicant_node['@data-format'];
                var sequence = applicant_node['@sequence'];
                var value = _.string.trim(applicant_node['applicant-name']['name']['$'], ', ');
                applicant_groups[data_format] = applicant_groups[data_format] || {};
                applicant_groups[data_format][sequence] = value;
                if (sequence > sequence_max)
                    sequence_max = sequence;
            });
            //console.log(applicant_groups);

            var applicants_list = [];
            _.each(_.range(1, parseInt(sequence_max) + 1), function(sequence) {
                sequence = sequence.toString();
                var epodoc_value = applicant_groups['epodoc'][sequence];
                var original_value = applicant_groups['original'][sequence];
                applicants_list.push(epodoc_value + ' / ' + original_value);
            });

            return applicants_list;
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

        // handle checkbox clicks by add-/remove-operations on basket
        $(".patent_number").click(function() {
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

OpsChooserApp.addInitializer(function(options) {
    var collectionView = new OpsExchangeDocumentCollectionView({
        collection: options.documents
    });
    OpsChooserApp.listRegion.show(collectionView);
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
        OpsChooserApp.search.perform(query, OpsChooserApp.documents);

    OpsChooserApp.start({documents: OpsChooserApp.documents});

});

$('input#query-button').click(function() {
    var querystring = $('textarea#query').val();
    //send to server and process response
    //alert(querystring);
    if (!_.isEmpty(querystring)) {
        OpsChooserApp.search.perform(querystring, OpsChooserApp.documents);
    }
});
