// -*- coding: utf-8 -*-
// (c) 2017 Andreas Motl, Elmyra UG
require('./base.js');

DepaTechSearch = DatasourceSearch.extend({
    url: '/api/depatech/published-data/search',
});

DepaTechResultEntry = Backbone.Model.extend({

    defaults: {
    },

});

DepaTechCrawler = DatasourceCrawler.extend({

    initialize: function(options) {
        log('DepaTechCrawler.initialize');
        options = options || {};
        options.datasource = 'depatech';
        this.__proto__.constructor.__super__.initialize.apply(this, arguments);
    },

});

// Register data source adapter with application
navigatorApp.addInitializer(function(options) {
    this.register_datasource('depatech', {

        // The title used when referencing this data source to the user
        title: 'depa.tech',

        // The data source adapter classes
        adapter: {
            search: DepaTechSearch,
            //crawl: DepaTechCrawler,
        },

        // Settings for query builder
        querybuilder: {

            // Hotkey for switching to this data source
            hotkey: 'ctrl+shift+t',

            // Which additional extra fields can be queried for
            extra_fields: ['pubdate'],

            // Which placeholders to use for comfort form demo criteria
            placeholder: {
                patentnumber: 'dpma',
                inventor: 'bosch',
            },

            // Bootstrap color variant used for referencing this data source in a query history entry
            history_label_color: 'success',

        },

    });
});
