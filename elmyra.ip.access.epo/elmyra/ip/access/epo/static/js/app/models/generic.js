// -*- coding: utf-8 -*-
// (c) 2013-2015 Andreas Motl, Elmyra UG

GenericExchangeDocument = OpsBaseModel.extend({

    defaults: _({}).extend(OpsBaseModel.prototype.defaults, OpsHelpers.prototype, {

        // TODO: maybe move these methods to "viewHelpers"
        // http://lostechies.com/derickbailey/2012/04/26/view-helpers-for-underscore-templates/
        // https://github.com/marionettejs/backbone.marionette/wiki/View-helpers-for-underscore-templates#using-this-with-backbonemarionette

        get_patent_number: function() {
            return this['@country'] + this['@doc-number'] + this['@kind'];
        },

        get_document_id: function() {
            var data = {
                country: this['@country'],
                docnumber: this['@doc-number'],
                kind: this['@kind'],
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

        parties_to_list: function(container, value_attribute_name) {
            return [];
        },

        has_ipc: function() {
            return false;
        },
        get_ipc_list: function(links) {
            return [];
        },

        has_ipcr: function() {
            return false;
        },
        get_ipcr_list: function(links) {
            return [];
        },

        has_classifications: function() {
            return false;
        },
        get_classification_schemes: function() {
            return ['CPC', 'UC', 'FI', 'FTERM'];
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

        get_publication_date: function() {
        },

        get_application_date: function() {
        },

    }),

    get_document_number: function() {
        return this.attributes.get_patent_number();
    },

});
