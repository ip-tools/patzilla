// -*- coding: utf-8 -*-
// (c) 2014-2018 Andreas Motl <andreas.motl@ip-tools.org>
'use strict';

const {DatasourceSearch, DatasourceCrawler} = require("../base");

export const SipSearch = DatasourceSearch.extend({
    url: '/api/sip/published-data/search',
});

export const SipResultEntry = Backbone.Model.extend({
    defaults: {
    },
});

export const SipCrawler = DatasourceCrawler.extend({

    crawler_limit: 5000,

    initialize: function(options) {
        log('SipCrawler.initialize');
        options = options || {};
        options.datasource = 'sip';
        this.__proto__.constructor.__super__.initialize.apply(this, arguments);
    },

});
