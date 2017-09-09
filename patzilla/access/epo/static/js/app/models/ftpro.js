// -*- coding: utf-8 -*-
// (c) 2014 Andreas Motl, Elmyra UG

FulltextProSearch = DatasourceSearch.extend({
    url: '/api/ftpro/published-data/search',
});

FulltextProResultEntry = Backbone.Model.extend({

    defaults: {
    },

});

FulltextProCrawler = DatasourceCrawler.extend({

    initialize: function(options) {
        log('FulltextProCrawler.initialize');
        options = options || {};
        options.datasource = 'ftpro';
        this.__proto__.constructor.__super__.initialize.apply(this, arguments);
    },

});
