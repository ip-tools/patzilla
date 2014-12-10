// -*- coding: utf-8 -*-
// (c) 2013,2014 Andreas Motl, Elmyra UG

PaginationView = Backbone.Marionette.ItemView.extend({
    tagName: 'div',
    template: _.template($('#ops-pagination-template').html(), this.model),

    initialize: function() {
        console.log('PaginationView.initialize');
        this.listenTo(this.model, "commit", this.render);
        this.listenTo(this, "item:rendered", this.setup_ui);
        this.templateHelpers.config = opsChooserApp.config;
    },

    templateHelpers: {},

    // Change Which Template Is Rendered For A View
    // https://github.com/marionettejs/backbone.marionette/blob/master/docs/marionette.view.md#change-which-template-is-rendered-for-a-view
    getTemplate: function(){
        if (opsChooserApp.config.get('mode') == 'liveview') {
            return '#ops-pagination-template-liveview';
        } else if (this.model.get('searchmode') == 'subsearch') {
            return '#ops-pagination-template';
        } else {
            return '#ops-pagination-template';
        }
    },

    setup_ui: function() {

        console.log('PaginationView.setup_ui');

        var _this = this;

        var datasource = this.model.get('datasource');
        var pagesize_choices = this.model.get('pagination_pagesize_choices');
        var page_size = this.model.get('page_size');
        var result_count = this.model.get('result_count');
        var maximum_results = this.get_maximum_results();
        var result_range = this.model.get('result_range');
        var current_page = this.model.get('pagination_current_page');

        // google workaround: let's assume 1000 results to make the paging work
        if (datasource == 'google' && result_count == null) {
            result_count = 1000;
        }

        // compute number of pagination entries
        var page_count = 0;
        if (result_count > 0 && page_size > 0) {
            var need_pages = result_count / page_size;
            if (need_pages >= 1) {
                page_count = Math.ceil(need_pages);
            }
            page_count = _.min([page_count, Math.ceil(maximum_results / page_size)]);
        }

        if (page_count < 1) {
            $('.page-size-chooser').parent().remove();
            return;
        }

        // 1. initialize pagination widget

        // workaround: create object, then destroy to detach event handlers
        // since setup_ui will get called multiple times

        $(this.el).find('.jqpagination').each(function(i, jqpagination) {

            $(this).jqPagination();
            $(this).jqPagination('destroy');

            // actually initialize widget properly
            $(this).jqPagination({
                max_page: page_count,
                current_page: current_page,

                // page-change occurred
                paged: function(page) {
                    _this.model.set('pagination_current_page', page);
                    var options = _this.get_range(page);
                    // TODO: untangle this by doing opsChooserApp.perform_listsearch right here!?
                    if (opsChooserApp.queryBuilderView.get_flavor() == 'numberlist' && opsChooserApp.metadata.get('reviewmode') != true) {
                        opsChooserApp.perform_numberlistsearch(options);
                    } else {
                        opsChooserApp.perform_search(options);
                    }

                    // scroll to first result entry
                    var scroll_target = $('.ops-collection-entry').first();
                    opsChooserApp.ui.scroll_smooth(scroll_target);
                },

                //link_string: '/?page={page_number}',
            });

        });


        // 2.a create page size chooser
        $(this.el).find('.page-size-chooser ul').each(function(i, page_size_chooser) {
            $(this).empty();
            var self = this;
            _(pagesize_choices).map(function(entry) {
                var icon = '';
                if (entry == page_size) {
                    icon = '<i class="icon-check"></i>';
                } else {
                    icon = '<i class="icon-check-empty"></i>';
                }
                var entry_html = _.template('<li><a href="" data-value="<%= entry %>"><%= icon %> <%= entry %></a></li>')({entry: entry, icon: icon});
                $(self).append(entry_html);
            });
        });

        // 2.b make links from page size chooser entries
        $(this.el).find('.page-size-chooser a').click(function(event) {
            event.preventDefault();
            var value = $(this).data('value');
            _this.model.set('page_size', value);
            opsChooserApp.perform_search({clear: true});
            return false;
        });

        // 2.c deactivate page size chooser
        if (this.model.get('searchmode') == 'subsearch') {
            $(this.el).find('.page-size-chooser > .dropdown-toggle').prop('disabled', true);
        }


        // 3.a create pagination entries
        $(this.el).find('.pagination ul').each(function(i, pagination) {
            $(this).empty();
            var self = this;
            _.range(1, page_count + 1).map(function(page) {
                var range = _this.get_range(page).range;
                var entry = _.template('<li><a href="" range="<%= range %>"><%= range %></a></li>')({range: range});
                $(self).append(entry);
            });
        });

        // 3.b make links from pagination entries
        $(this.el).find('.pagination a').click(function() {
            //var action = $(this).attr('action');
            var range = $(this).attr('range');
            opsChooserApp.perform_search({range: range});
            return false;
        });

        // 3.c mark proper pagination entry as active
        $(this.el).find('.pagination').find('a').each(function(i, anchor) {
            var anchor_range = $(anchor).attr('range');
            if (anchor_range == result_range) {
                var li = $(anchor).parent();
                li.addClass('active');
            }
        });

    },

    onDomRefresh: function() {
        console.log('PaginationView.onDomRefresh');
    },

    get_maximum_results: function() {
        var datasource = this.model.get('datasource');
        var maximum_results = this.model.get('maximum_results')[datasource] || Infinity;
        return maximum_results;
    },

    get_range: function(page) {
        var page_size = this.model.get('page_size');
        //log('page_size:', page_size);
        var range_begin = (page - 1) * page_size + 1;
        var range_end = range_begin + page_size - 1;

        // limit range_end to maximum results per datasource
        range_end = _.min([range_end, this.get_maximum_results()]);

        var range = range_begin + '-' + range_end;
        return {range: range, range_begin: range_begin, range_end: range_end, page: page};
    },

});
