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
        return this.fetch({
            //async: false,
            data: $.param(query_parameters),
            success: function (payload, response, options) {
                opsChooserApp.ui.indicate_activity(false);
                opsChooserApp.ui.reset_content();
                self.keywords = jQuery.parseJSON(options.xhr.getResponseHeader('X-Elmyra-Query-Keywords'));
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
