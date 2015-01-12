// -*- coding: utf-8 -*-
// (c) 2014 Andreas Motl, Elmyra UG

FulltextProSearch = DatasourceSearch.extend({
    url: '/api/ftpro/published-data/search',
});

FulltextProResultEntry = Backbone.Model.extend({

    defaults: {
    },

});

FulltextProCrawler = Marionette.Controller.extend({

    initialize: function(options) {
        log('FulltextProCrawler.initialize');
        options = options || {};
        this.query = options.query;
        this.constituents = options.constituents;
    },

    crawl: function() {
        var deferred = $.Deferred();
        var url_tpl = _.template('/api/ftpro/published-data/crawl/<%= constituents %>?query=<%= query %>');
        var url = url_tpl({constituents: this.constituents, query: this.query});
        var _this = this;
        $.ajax({url: url, async: true})
            .success(function(payload) {
                if (payload) {
                    if (_this.constituents == 'pub-number') {
                        var numberlist = payload['numbers'];
                        deferred.resolve(numberlist);
                    } else {
                        deferred.reject('Unknown constituents "' + _this.constituents + '"');
                    }
                } else {
                    deferred.reject('Empty response');
                }
            }).error(function(error) {
                deferred.reject('API failed', error);
            });
        return deferred;
    },

});
