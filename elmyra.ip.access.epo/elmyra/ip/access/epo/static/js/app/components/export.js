// -*- coding: utf-8 -*-
// (c) 2015 Andreas Motl, Elmyra UG

ResultNumbersView = Backbone.Marionette.ItemView.extend({

    tagName: "div",
    id: "result-numbers-view",
    className: "modal",
    template: "#result-numbers-template",

    initialize: function() {
        console.log('ResultNumbersView.initialize');
    },

    indicate_activity: function(active) {
        if (active) {
            this.$el.find('#result-numbers-busy').show();
            this.$el.find('#result-numbers-ready').hide();

        } else {
            this.$el.find('#result-numbers-busy').hide();
            this.$el.find('#result-numbers-ready').show();
        }
    },

    user_message: function(message, kind) {
        $('#result-numbers-info').empty();
        return opsChooserApp.ui.user_alert(message, kind, '#result-numbers-info');
    },

    templateHelpers: {
    },

    setup_copy_button: function(payload) {
        var copy_button = this.$el.find('#result-numbers-copy-button');
        _ui.copy_to_clipboard_bind_button('text/plain', payload, {element: copy_button[0], wrapper: this.el});
    },

    onShow: function() {

        var datasource_whitelist = ['ops'];
        var datasource = this.model.get('datasource');
        if (!_(datasource_whitelist).contains(datasource)) {
            this.user_message('Fetching result publication numbers for datasource "' + datasource + '" not implemented yet.', 'error');
            return;
        }

        var query = this.model.get('query_origin');

        this.indicate_activity(true);
        this.user_message('Fetching result numbers for query "' + query + '", please stand by. &nbsp; <i class="spinner icon-refresh icon-spin"></i>', 'info');

        var url = '/api/ops/published-data/crawl/pub-number?query=' + query;
        var _this = this;
        $.ajax({url: url, async: true})
            .success(function(payload) {
                if (payload) {

                    // display numberlist payload in textarea
                    var numberlist = payload['ops:world-patent-data']['ops:biblio-search']['ops:search-result']['publication-numbers'];
                    var numberlist_string = numberlist.join('\n');
                    $('#result-numbers-content').val(numberlist_string);

                    _this.setup_copy_button(numberlist_string);

                    // notify user
                    _this.indicate_activity(false);
                    _this.user_message('Result publication numbers fetched successfully. Hits: ' + numberlist.length, 'success');
                }
            }).error(function(error) {

                // notify user
                var message =
                    'Error while crawling numberlist for query "' + query +
                        '" at datasource "' + _this.model.get('datasource') + '".';
                console.warn(message, error);
                _this.indicate_activity(false);
                _this.user_message(message, 'error');
            });

    },

    events: {
    },

});
