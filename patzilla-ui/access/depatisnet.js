// -*- coding: utf-8 -*-
// (c) 2014 Andreas Motl, Elmyra UG
require('./base.js');

DepatisnetSearch = DatasourceSearch.extend({
    url: '/api/depatisnet/published-data/search',
});

DepatisnetCrawler = DatasourceCrawler.extend({

    initialize: function(options) {
        log('DepatisnetCrawler.initialize');
        options = options || {};
        options.datasource = 'depatisnet';
        this.__proto__.constructor.__super__.initialize.apply(this, arguments);
    },

});

DepatisConnectFulltext = Marionette.Controller.extend({

    initialize: function(document_number) {
        log('DepatisConnectFulltext.initialize');
        this.document_number = document_number;
    },

    get_datasource_label: function() {
        return 'DPMA/DEPATISnet';
    },

    get_claims: function() {

        var _this = this;
        var deferred = $.Deferred();

        var url = _.template('/api/depatisconnect/<%= document_number %>/claims')({ document_number: this.document_number});
        $.ajax({url: url, async: true}).success(function(payload) {
            if (payload) {
                var response = {
                    html: payload['xml'],
                    lang: payload['lang'],
                };
                deferred.resolve(response, _this.get_datasource_label());
            }
        }).error(function(error) {
            console.warn('Error while fetching claims from DEPATISconnect for', _this.document_number, error);
            deferred.resolve({html: 'No data available'});
        });

        return deferred.promise();

    },

    get_description: function() {

        var _this = this;
        var deferred = $.Deferred();

        var url = _.template('/api/depatisconnect/<%= document_number %>/description')({ document_number: this.document_number});
        $.ajax({url: url, async: true})
            .success(function(payload) {
                if (payload) {
                    var response = {
                        html: payload['xml'],
                        lang: payload['lang'],
                    };
                    deferred.resolve(response, _this.get_datasource_label());
                }
            }).error(function(error) {
                console.warn('Error while fetching description from DEPATISconnect for', _this.document_number, error);
                deferred.resolve({html: 'No data available'});
            });

        return deferred.promise();

    },

    get_abstract: function(language) {

        var _this = this;
        var deferred = $.Deferred();

        var url_tpl = '/api/depatisconnect/<%= document_number %>/abstract'
        if (language) {
            url_tpl += '?language=<%= language %>'
        }
        var url = _.template(url_tpl)({ document_number: this.document_number, language: language});
        $.ajax({url: url, async: true})
            .success(function(payload) {
                if (payload && payload['xml']) {
                    var response = {
                        html: payload['xml'],
                        lang: payload['lang'],
                    };
                    deferred.resolve(response);

                } else {
                    console.warn('DEPATISconnect: Empty abstract for', _this.document_number);
                    deferred.reject({html: 'Abstract for this document is empty, see original data source'});
                }
            }).error(function(error) {
                console.warn('DEPATISconnect: Error while fetching abstract for', _this.document_number, error);
                deferred.reject({html: 'No data available', error: error});
            });

        return deferred.promise();

    },

});
