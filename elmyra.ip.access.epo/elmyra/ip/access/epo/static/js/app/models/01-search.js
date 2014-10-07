// -*- coding: utf-8 -*-
// (c) 2014 Andreas Motl, Elmyra UG

DatasourceSearch = Backbone.Model.extend({
    keywords: [],
    perform: function(query, range) {

        opsChooserApp.ui.indicate_activity(true);

        var self = this;
        return this.fetch({
            //async: false,
            data: $.param({ query: query, range: range}),
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

                $('#alert-area').empty();
                try {
                    var response = jQuery.parseJSON(xhr.responseText);
                    if (response['status'] == 'error') {
                        _.each(response['errors'], function(error) {
                            var tpl = _.template($('#cornice-error-template').html());
                            var alert_html = tpl(error);
                            $('#alert-area').append(alert_html);
                        });
                        $(".very-short").shorten({showChars: 0, moreText: 'more', lessText: 'less'});

                    }

                    // SyntaxError when decoding from JSON fails
                } catch (err) {
                    // TODO: display more details of xhr response (headers, body, etc.)
                    // TODO: use class="alert alert-error alert-block"
                    var response = xhr.responseText;
                    $('#alert-area').append(response);
                }

            }
        });

    },
});
