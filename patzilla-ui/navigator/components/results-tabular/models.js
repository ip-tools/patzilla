// -*- coding: utf-8 -*-
// (c) 2014-2018 Andreas Motl <andreas.motl@ip-tools.org>

ResultEntry = Backbone.Model.extend({
    defaults: {
    },
});


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
        var entry_class = navigatorApp.current_datasource_info().adapter.entry || ResultEntry;
        var model = new entry_class(attrs, options);
        return model;
    },

});
