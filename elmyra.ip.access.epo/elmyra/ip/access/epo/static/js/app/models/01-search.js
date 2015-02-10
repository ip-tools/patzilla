// -*- coding: utf-8 -*-
// (c) 2014 Andreas Motl, Elmyra UG

DatasourceSearch = Backbone.Model.extend({
    keywords: [],
    perform: function(query, options) {

        var query_parameters = { query: query };
        _.extend(query_parameters, options);
        log('DatasourceSearch.query_parameters:', query_parameters);

        opsChooserApp.ui.indicate_activity(true);

        var self = this;
        var _options = options;
        return this.fetch({
            //async: false,
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
