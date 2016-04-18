// -*- coding: utf-8 -*-
// (c) 2015 Andreas Motl, Elmyra UG

IFIClaimsSearch = DatasourceSearch.extend({
    url: '/api/ifi/published-data/search',
});

IFIClaimsResultEntry = Backbone.Model.extend({

    defaults: {
    },

});

IFIClaimsCrawler = DatasourceCrawler.extend({

    initialize: function(options) {
        log('IFIClaimsCrawler.initialize');
        options = options || {};
        options.datasource = 'ifi';
        this.__proto__.constructor.__super__.initialize.apply(this, arguments);
    },

});
