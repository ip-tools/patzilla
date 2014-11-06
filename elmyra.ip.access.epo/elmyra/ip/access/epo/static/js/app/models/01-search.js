// -*- coding: utf-8 -*-
// (c) 2014 Andreas Motl, Elmyra UG

DatasourceSearch = Backbone.Model.extend({
    keywords: [],
    perform: function(query, options) {

        var query_parameters = { query: query };
        _.extend(query_parameters, options);
        log('search: query_parameters:', query_parameters);

        opsChooserApp.ui.indicate_activity(true);

        var self = this;
        var _options = options;
        return this.fetch({
            //async: false,
            data: $.param(query_parameters),
            success: function (payload, response, options) {
                opsChooserApp.ui.indicate_activity(false);
                opsChooserApp.ui.reset_content();
                var keywords = options.xhr.getResponseHeader('X-Elmyra-Query-Keywords');

                if (keywords) {
                    // fix for weird Chrome bug: "X-Elmyra-Query-Keywords" headers are recieved duplicated
                    keywords = keywords.replace(/(.+), \[.+\]/, '$1');
                    self.keywords = jQuery.parseJSON(keywords);
                }

                // fallback keyword gathering from comfort form
                if (_.isEmpty(self.keywords)) {
                    var keywords_json = _options.keywords;
                    if (keywords_json) {
                        self.keywords = jQuery.parseJSON(keywords_json);
                        log('keywords fallback:', self.keywords);
                    }
                }

            },
            error: function(e, xhr) {

                //console.log("error: " + xhr.responseText);
                opsChooserApp.ui.indicate_activity(false);
                opsChooserApp.ui.reset_content();
                opsChooserApp.documents.reset();

                opsChooserApp.ui.propagate_alerts(xhr.responseText);
            }
        });

    },
});
