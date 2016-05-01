// -*- coding: utf-8 -*-
// (c) 2014 Andreas Motl, Elmyra UG

ResultCollection = Backbone.Collection.extend({

    initialize: function(collection) {
        this.document_numbers = [];
    },

    set_reference_document_numbers: function(document_numbers) {
        this.reference_document_numbers = document_numbers;
    },

    set_placeholder_document_numbers: function(document_numbers) {
        this.placeholder_document_numbers = document_numbers;
    },

    model: function(attrs, options) {
        if (attrs.upstream_provider == 'ftpro') {
            return new FulltextProResultEntry(attrs, options);
        } else if (attrs.upstream_provider == 'ifi') {
            log('Make IFIClaimsResultEntry');
            return new IFIClaimsResultEntry(attrs, options);
        } else {
            console.warn('Could not create result model instance for upstream provider "' + attrs.upstream_provider + '"');
        }
    },

});
