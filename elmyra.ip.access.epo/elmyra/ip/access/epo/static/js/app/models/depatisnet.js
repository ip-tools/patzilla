// -*- coding: utf-8 -*-
// (c) 2014 Andreas Motl, Elmyra UG

DepatisnetSearch = DatasourceSearch.extend({
    url: '/api/depatisnet/published-data/search',
});

DepatisConnectFulltext = Marionette.Controller.extend({

    initialize: function(document_number) {
        log('DepatisConnectFulltext.initialize');
        this.document_number = document_number;
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
                deferred.resolve(response);
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
                    deferred.resolve(response);
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
                if (payload) {
                    var response = {
                        html: payload['xml'],
                        lang: payload['lang'],
                    };
                    deferred.resolve(response);
                }
            }).error(function(error) {
                console.warn('Error while fetching description from DEPATISconnect for', _this.document_number, error);
                deferred.resolve({html: 'No data available'});
            });

        return deferred.promise();

    },

});
