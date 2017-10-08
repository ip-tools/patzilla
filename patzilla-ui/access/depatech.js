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
