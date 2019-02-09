// -*- coding: utf-8 -*-
// (c) 2015,2018 Andreas Motl <andreas.motl@ip-tools.org>
require('patzilla.navigator.components.results-dialog');

const ModalRegion = require('patzilla.lib.marionette').ModalRegion;


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

        // Generic data source adapters
        if (navigatorApp.has_datasource(datasource)) {
            var datasource_info = navigatorApp.datasource_info(datasource);
            var crawler_class = datasource_info.adapter.crawl;
            if (crawler_class) {
                this.crawler_limit = crawler_class.crawler_limit;
            } else {
                this.user_message('Fetching publication numbers for datasource "' + datasource + '" not implemented yet.', 'error');
            }
        } else {
            this.user_message('Search provider "' + datasource + '" not implemented.', {type: 'error', icon: 'icon-search'});
        }

        var crawler = new crawler_class({constituents: 'pub-number', query: query, query_data: query_data, filter: filter})
        return crawler;

    },

    show: function() {

        // Sanity check: Don't share dirty queries
        if (navigatorApp.queryBuilderView.check_data_is_dirty({'icon': 'icon-download'})) { return; }

        // Sanity check: Do we have valid query criteria
        if (!this.has_criteria()) {
            navigatorApp.ui.notify('Empty search criteria', {type: 'warning', icon: 'icon-download'});
            return;
        }

        // Display dialog
        var modal = new ModalRegion({el: '#modal-area'});
        modal.show(this);
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

            // Display numberlist widget
            var result_numbers_view = new ResultNumbersView({model: _this.metadata});
            result_numbers_view.show();
        });

        $('#fetch-result-numbers-no-kindcodes-action').off('click');
        $('#fetch-result-numbers-no-kindcodes-action').on('click', function(e) {

            // Set signal to apply filter "strip_kindcodes" on response
            _this.metadata.set('filter', {'strip_kindcodes': true});

            // Display numberlist widget
            var result_numbers_view = new ResultNumbersView({model: _this.metadata});
            result_numbers_view.show();

        });

    });

    this.register_component('crawler');

});
