// -*- coding: utf-8 -*-
// (c) 2015 Andreas Motl, Elmyra UG

ResultNumbersView = GenericResultView.extend({

    initialize: function() {
        console.log('ResultNumbersView.initialize');
        this.message_more = '';
        this.crawler_limit = 0;
    },

    setup_data: function(data) {

        var numberlist = data;

        var numberlist_string = numberlist.join('\n');

        // transfer to textarea
        $('#result-content').val(numberlist_string);

        this.setup_numberlist_buttons(numberlist);

        if (numberlist.length >= this.crawler_limit) {
            var datasource = this.model.get('datasource');
            this.message_more += '<br/>' +
                'Remark: The maximum number of result items for datasource "' + datasource + '" is "' + this.crawler_limit + '".';
        }

    },

    fetcher_factory: function() {

        var query = this.model.get('query_origin');
        var query_data = this.model.get('query_data');
        var datasource = this.model.get('datasource');
        var filter = this.model.get('filter');

        // compute crawler by datasource
        var crawler_class;
        var crawler_limit;
        if (datasource == 'ops') {
            crawler_class = OpsPublishedDataCrawler;
            this.crawler_limit = 2000;

        } else if (datasource == 'depatisnet') {
            crawler_class = DepatisnetCrawler;
            this.crawler_limit = 1000;

        } else if (datasource == 'ftpro') {
            crawler_class = FulltextProCrawler;
            this.crawler_limit = 5000;

        } else if (datasource == 'sdp') {
            crawler_class = SdpCrawler;
            this.crawler_limit = 50000;

        } else {
            this.user_message('Fetching publication numbers for datasource "' + datasource + '" not implemented yet.', 'error');
            return;

        }

        var crawler = new crawler_class({constituents: 'pub-number', query: query, query_data: query_data, filter: filter})
        return crawler;

    },

});


opsChooserApp.addInitializer(function(options) {

    this.listenTo(this, 'metadataview:setup_ui', function() {
        var _this = this;

        // wire fetch-results buttons
        $('#fetch-result-numbers-action').unbind('click');
        $('#fetch-result-numbers-action').click(function(e) {
            var modal = new ModalRegion({el: '#modal-area'});
            // reset all filters
            _this.metadata.set('filter', {});
            var result_numbers_view = new ResultNumbersView({model: _this.metadata});
            modal.show(result_numbers_view);
        });
        $('#fetch-result-numbers-no-kindcodes-action').unbind('click');
        $('#fetch-result-numbers-no-kindcodes-action').click(function(e) {
            var modal = new ModalRegion({el: '#modal-area'});
            // apply filter "strip_kindcodes" on response
            _this.metadata.set('filter', {'strip_kindcodes': true});
            var result_numbers_view = new ResultNumbersView({model: _this.metadata});
            modal.show(result_numbers_view);
        });

    });

});
