// -*- coding: utf-8 -*-
// (c) 2014 Andreas Motl, Elmyra UG

DepatisnetSearch = Backbone.Model.extend({
    url: '/api/depatisnet/published-data/search',
    keywords: [],
    perform: function(query, range) {

        indicate_activity(true);

        var self = this;
        return this.fetch({
            //async: false,
            data: $.param({ query: query, range: range}),
            success: function (payload, response, options) {
                indicate_activity(false);
                reset_content();
                self.keywords = jQuery.parseJSON(options.xhr.getResponseHeader('X-Elmyra-Query-Keywords'));
            },
            error: function(e, xhr) {

                //console.log("error: " + xhr.responseText);
                indicate_activity(false);
                reset_content();
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

});
