// -*- coding: utf-8 -*-
// (c) 2015 Andreas Motl, Elmyra UG
require('patzilla.lib.marionette-modalregion');
require('patzilla.navigator.components.results-dialog');

ResultNumbersView = GenericResultView.extend({

    initialize: function() {
        console.log('ResultNumbersView.initialize');
        this.message_more = '';
        this.crawler_limit = 0;
    },

    setup_data: function(data) {

        var datasource = this.model.get('datasource');
        var numberlist = data;

        if (!numberlist) {
            this.message_more += '<br/>' +
                'Remark: No result items from datasource "' + datasource + '".';
            return;
        }

        var numberlist_string = numberlist.join('\n');

        // transfer to textarea
        $('#result-content').val(numberlist_string);

        this.setup_numberlist_buttons(numberlist);

        if (numberlist.length >= this.crawler_limit) {
            this.message_more += '<br/>' +
                'Remark: The maximum number of result items for datasource "' + datasource + '" is "' + this.crawler_limit + '".';
        }

    },

    has_criteria: function() {
        return Boolean(this.model.get('query_origin'));
    },

    fetcher_factory: function() {

        var query = this.model.get('query_origin');
        var query_data = this.model.get('query_data');
        var datasource = this.model.get('datasource');
        var filter = this.model.get('filter');

        // compute crawler by datasource
        var crawler_class;
        if (datasource == 'ops') {
            crawler_class = OpsPublishedDataCrawler;
            this.crawler_limit = 2000;

        } else if (datasource == 'depatisnet') {
            crawler_class = DepatisnetCrawler;
            this.crawler_limit = 1000;

        } else if (datasource == 'ftpro') {
            crawler_class = FulltextProCrawler;
            this.crawler_limit = 5000;

        } else if (datasource == 'ifi') {
            crawler_class = IFIClaimsCrawler;
            this.crawler_limit = 50000;

        } else {
            this.user_message('Fetching publication numbers for datasource "' + datasource + '" not implemented yet.', 'error');
            return;

        }

        var crawler = new crawler_class({constituents: 'pub-number', query: query, query_data: query_data, filter: filter})
        return crawler;

    },

});


navigatorApp.addInitializer(function(options) {

    this.listenTo(this, 'metadataview:setup_ui', function() {
        var _this = this;

        // wire fetch-results buttons
        $('#fetch-result-numbers-action').off('click');
        $('#fetch-result-numbers-action').on('click', function(e) {

            // Reset all filters
            _this.metadata.set('filter', {});
            var result_numbers_view = new ResultNumbersView({model: _this.metadata});

            // Sanity checks
            if (!result_numbers_view.has_criteria()) {
                navigatorApp.ui.notify('Empty search criteria', {type: 'warning', icon: 'icon-download'});
                return;
            }

            // Display dialog
            var modal = new ModalRegion({el: '#modal-area'});
            modal.show(result_numbers_view);
        });

        $('#fetch-result-numbers-no-kindcodes-action').off('click');
        $('#fetch-result-numbers-no-kindcodes-action').on('click', function(e) {

            // Reset all filters
            // Set signal to apply filter "strip_kindcodes" on response
            _this.metadata.set('filter', {'strip_kindcodes': true});
            var result_numbers_view = new ResultNumbersView({model: _this.metadata});

            // Sanity checks
            if (!result_numbers_view.has_criteria()) {
                navigatorApp.ui.notify('Empty search criteria', {type: 'warning', icon: 'icon-download'});
                return;
            }

            // Display dialog
            var modal = new ModalRegion({el: '#modal-area'});
            modal.show(result_numbers_view);

        });

    });

    this.register_component('crawler');

});
