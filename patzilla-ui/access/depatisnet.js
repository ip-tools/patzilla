// -*- coding: utf-8 -*-
// (c) 2014 Andreas Motl, Elmyra UG
require('./base.js');

DepatisnetSearch = DatasourceSearch.extend({
    url: '/api/depatisnet/published-data/search',
});

DepatisnetCrawler = DatasourceCrawler.extend({

    crawler_limit: 1000,

    initialize: function(options) {
        log('DepatisnetCrawler.initialize');
        options = options || {};
        options.datasource = 'depatisnet';
        this.__proto__.constructor.__super__.initialize.apply(this, arguments);
    },

});

// Register data source adapter with application
navigatorApp.addInitializer(function(options) {
    this.register_datasource('depatisnet', {

        // The title used when referencing this data source to the user
        title: 'DPMA',

        // The data source adapter classes
        adapter: {
            search: DepatisnetSearch,
            crawl: DepatisnetCrawler,
        },

        // Settings for query builder
        querybuilder: {

            // Hotkey for switching to this data source
            hotkey: 'ctrl+shift+d',

            // Which additional extra fields can be queried for
            extra_fields: ['pubdate', 'appdate', 'priodate', 'citation'],

            // Whether to enable the expression syntax chooser
            enable_syntax_chooser: true,

            // Enable sorting feature
            enable_sorting: true,

            // Enable the "remove/replace family members" feature
            enable_remove_replace_family_members: true,

            // Bootstrap color variant used for referencing this data source in a query history entry
            history_label_color: 'inverse',

        },

    });
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
        $.ajax({url: url, async: true})
            .then(function(payload) {
                if (payload) {
                    var response = {
                        html: payload['xml'],
                        lang: payload['lang'],
                    };
                    deferred.resolve(response, _this.get_datasource_label());
                }
            }).catch(function(error) {
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
            .then(function(payload) {
                if (payload) {
                    var response = {
                        html: payload['xml'],
                        lang: payload['lang'],
                    };
                    deferred.resolve(response, _this.get_datasource_label());
                }
            }).catch(function(error) {
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
            .then(function(payload) {
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
            }).catch(function(error) {
                console.warn('DEPATISconnect: Error while fetching abstract for', _this.document_number, error);
                deferred.reject({html: 'No data available', error: error});
            });

        return deferred.promise();

    },

});
