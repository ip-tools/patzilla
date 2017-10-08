// -*- coding: utf-8 -*-
// (c) 2013-2017 Andreas Motl, Elmyra UG
require('./10-ops-base.js');

GenericExchangeDocument = Backbone.Model.extend({});

_.extend(GenericExchangeDocument.prototype, OpsBaseModel.prototype, OpsHelpers.prototype, {

    get_datasource_label: function() {
        return undefined;
    },

    get_patent_number: function() {
        return this.get_document_id().fullnumber;
    },

    get_document_id: function() {
        var data = {
            country: this.get('@country'),
            docnumber: this.get('@doc-number'),
            kind: this.get('@kind'),
        };
        data.fullnumber = (data.country || '') + (data.docnumber || '') + (data.kind || '');
        return data;
    },

    get_document_number: function() {
        return this.get_patent_number();
    },

    get_publication_number: function(format) {
        var document_id = this.get_publication_reference(format);
        return document_id.fullnumber;
    },

    get_application_number: function(format) {
        var document_id = this.get_application_reference(format);
        return document_id.fullnumber;
    },

    get_full_cycle: function() {
        return [];
    },

    get_full_cycle_numbers: function() {
        return [];
    },

    get_publication_reference: function(format) {
        return this.get_document_id();
    },

    get_application_reference: function(format) {
        return this.get_document_id();
    },

    get_patent_citation_list: function(links, id_type) {
        return [];
    },

    get_title_list: function() {
        return [];
    },

    get_abstract_list: function() {
        return [];
    },

    get_applicants: function(links) {
        return [];
    },

    get_inventors: function(links) {
        return [];
    },

    get_classification_schemes: function() {
        return ['IPC', 'IPC-R', 'CPC', 'UC', 'FI', 'FTERM'];
    },
    get_classifications: function(links) {
        return {};
    },

    get_priority_claims: function(links) {
        return [];
    },
    get_application_references: function(links) {
    },

    has_citations: function() {
        return false;
    },

    get_citing_query: function() {
        var query = 'ct=' + this.get_publication_number('epodoc');
        return query;
    },
    get_same_citations_query: function() {
        var items = this.get_patent_citation_list(false, 'epodoc');
        return this.get_items_query(items, 'ct', 'OR');
    },
    get_all_citations_query: function() {
        var items = this.get_patent_citation_list(false, 'epodoc');
        return this.get_items_query(items, 'pn', 'OR');
    },
    get_items_query: function(items, fieldname, operator) {
        // FIXME: limit query to 10 items due to ops restriction
        items = items.slice(0, 10);
        items = items.map(function(item) { return fieldname + '=' + item; });
        var query = items.join(' ' + operator + ' ');
        return query;
    },

    get_npl_citation_list: function() {
        return [];
    },

    has_fulltext: function() {
        return false;
    },

    has_full_cycle: function() {
        return false;
    },

    get_publication_date: function() {
    },

    get_application_date: function() {
    },

});
