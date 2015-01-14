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

        // compute crawler by datasource
        var crawler_class;
        var crawler_limit;
        var datasource = this.model.get('datasource');
        if (datasource == 'ops') {
            crawler_class = OpsPublishedDataCrawler;
            crawler_limit = 2000;

        } else if (datasource == 'depatisnet') {
            crawler_class = DepatisnetCrawler;
            crawler_limit = 1000;

        } else if (datasource == 'ftpro') {
            crawler_class = FulltextProCrawler;
            crawler_limit = 5000;

        } else {
            this.user_message('Fetching publication numbers for datasource "' + datasource + '" not implemented yet.', 'error');
            return;

        }

        var query = this.model.get('query_origin');

        this.indicate_activity(true);
        this.user_message('Fetching result numbers for query "' + query + '", please stand by. &nbsp; <i class="spinner icon-refresh icon-spin"></i>', 'info');

        var _this = this;
        var crawler = new crawler_class({constituents: 'pub-number', query: query})
        crawler.crawl().then(function(numberlist) {

                // transfer data
                var numberlist_string = numberlist.join('\n');
                $('#result-numbers-content').val(numberlist_string);

                _this.setup_copy_button(numberlist_string);

                // notify user
                _this.indicate_activity(false);
                var message = numberlist.length + ' result publication numbers fetched successfully.';
                if (numberlist.length >= crawler_limit) {
                    message += '<br/>' +
                        'Remark: The maximum number of results for datasource "' + datasource + '" is "' + crawler_limit + '".';
                }
                _this.user_message(message, 'success');

            }).fail(function(message, error) {

                // notify user
                _this.indicate_activity(false);

                var message =
                    'Error while crawling numberlist for query "' + query +
                        '" at datasource "' + _this.model.get('datasource') + '".' + '<br/>' + message;
                _this.user_message(message, 'error');
                console.warn(message, error);

            });

    },

    events: {
    },

});


opsChooserApp.addInitializer(function(options) {

    this.listenTo(this, 'results:ready', function() {
        var _this = this;
        // wire fetch-results button
        $('#fetch-result-numbers-action').unbind('click');
        $('#fetch-result-numbers-action').click(function() {
            var modal = new ModalRegion({el: '#modal-area'});
            var result_numbers_view = new ResultNumbersView({model: _this.metadata});
            modal.show(result_numbers_view);
        });

    });

});
