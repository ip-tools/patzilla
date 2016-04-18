// -*- coding: utf-8 -*-
// (c) 2015 Andreas Motl, Elmyra UG

SdpSearch = DatasourceSearch.extend({
    url: '/api/sdp/published-data/search',
});

SdpResultEntry = Backbone.Model.extend({

    defaults: {
    },

});

SdpCrawler = DatasourceCrawler.extend({

    initialize: function(options) {
        log('SdpCrawler.initialize');
        options = options || {};
        options.datasource = 'sdp';
        this.__proto__.constructor.__super__.initialize.apply(this, arguments);
    },

});
