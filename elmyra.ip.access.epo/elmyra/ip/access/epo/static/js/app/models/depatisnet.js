// -*- coding: utf-8 -*-
// (c) 2014 Andreas Motl, Elmyra UG

DepatisnetSearch = Backbone.Model.extend({
    url: '/api/depatisnet/published-data/search',
    keywords: [],
    perform: function(query, range) {

        var self = this;
        return this.fetch({
            //async: false,
            data: $.param({ query: query, range: range}),
            success: function (payload, response, options) {
                self.keywords = jQuery.parseJSON(options.xhr.getResponseHeader('X-Elmyra-Query-Keywords'));
            },
            error: function(e, xhr) {

                //console.log("error: " + xhr.responseText);
                reset_content();

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
