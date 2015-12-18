// -*- coding: utf-8 -*-
// (c) 2014 Andreas Motl, Elmyra UG

DatasourceSearch = Backbone.Model.extend({
    keywords: [],
    perform: function(query, options) {

        var query_parameters = { query: query };
        _.extend(query_parameters, options);

        // debugging
        log('DatasourceSearch.query_parameters:', query_parameters);
        //log('params:', $.param(query_parameters));

        opsChooserApp.ui.indicate_activity(true);

        var self = this;
        var _options = options;
        return this.fetch({
            //async: false,
            // TODO: switch to JSON POST
            //method: 'post',
            data: $.param(query_parameters),
            success: function (payload, response, options) {
                opsChooserApp.ui.indicate_activity(false);
                //opsChooserApp.ui.reset_content();

                // decode regular keywords
                var keywords_regular = options.xhr.getResponseHeader('X-Elmyra-Query-Keywords');
                if (keywords_regular) {
                    self.keywords = self.decode_header_json(keywords_regular) || [];
                }

                // fallback keyword gathering from comfort form
                if (_.isEmpty(self.keywords)) {
                    var keywords_form = _options.keywords;
                    self.keywords = self.decode_header_json(keywords_form) || [];
                }

            },
            error: function(e, xhr) {

                console.log("DatasourceSearch error: " + xhr.responseText);

                opsChooserApp.ui.indicate_activity(false);
                opsChooserApp.ui.reset_content({documents: true});

                opsChooserApp.ui.propagate_alerts(xhr, {url: self.url});
            }
        });

    },

    decode_header_json: function(raw) {

        // workaround for weird Chrome bug: "X-Elmyra-Query-Keywords" headers are recieved duplicated
        // example: ["siemens", "bosch"], ["siemens", "bosch"]

        if (raw) {
            // wrap in yet another list
            raw = '[' + raw + ']';
            var data = jQuery.parseJSON(raw);
            if (!_.isEmpty(data)) {
                return data[0];
            }
        }
    },

});


DatasourceCrawler = Marionette.Controller.extend({

    initialize: function(options) {
        log('DatasourceCrawler.initialize');
        options = options || {};
        this.datasource = options.datasource;
        this.query = options.query;
        this.constituents = options.constituents;
        this.query_data = options.query_data || {};
        this.filter = options.filter || {};
    },

    start: function() {
        var deferred = $.Deferred();
        var more_params = $.param({
            'query_data': this.query_data,
        });
        var url_tpl = _.template('/api/<%= datasource %>/published-data/crawl/<%= constituents %>?query=<%= query %>&<%= more_params %>');
        var url = url_tpl({
            datasource: this.datasource,
            constituents: this.constituents,
            query: encodeURIComponent(this.query),
            more_params: more_params,
        });
        //log('url:', url);

        var _this = this;
        $.ajax({url: url, async: true})
            .success(function(payload) {
                if (payload) {
                    if (_this.constituents == 'pub-number') {
                        var numberlist = payload['numbers'];

                        // apply arbitrary named filter to numberlist
                        numberlist = _this.apply_filter(numberlist);

                        deferred.resolve(numberlist);
                    } else {
                        deferred.reject('Unknown constituents "' + _this.constituents + '"');
                    }
                } else {
                    deferred.reject('Empty response');
                }
            }).error(function(error) {
                deferred.reject('API failed: ' + JSON.stringify(error));
            });
        return deferred;
    },

    apply_filter: function(numberlist) {

        // strip patent kindcode from all numberlist items,
        // then build list of unique entries
        if (this.filter.strip_kindcodes) {
            numberlist = _(numberlist).map(function(item) {

                // strip patent kindcode for the poorest
                var re = /.+\d+(\D)/g;
                var match = re.exec(item);
                if (match[1]) {
                    var position = re.lastIndex;
                    if (position) {
                        item = item.substring(0, position - 1);
                    }
                }
                return item;
            });
            numberlist = _(numberlist).uniq();
        }
        return numberlist;
    },

});
