// -*- coding: utf-8 -*-
// (c) 2013,2014 Andreas Motl, Elmyra UG

PaginationView = Backbone.Marionette.ItemView.extend({
    tagName: 'div',
    template: '#ops-pagination-template',

    initialize: function() {
        console.log('PaginationView.initialize');
        this.listenTo(this.model, "commit", this.render);
        this.listenTo(this, "item:rendered", this.setup_ui);
    },

    // Change Which Template Is Rendered For A View
    // https://github.com/marionettejs/backbone.marionette/blob/master/docs/marionette.view.md#change-which-template-is-rendered-for-a-view
    getTemplate: function(){
        if (opsChooserApp.config.get('mode') == 'liveview'){
            return '#ops-pagination-template-liveview';
        } else if (this.model.get('searchmode') == 'subsearch'){
            return '#ops-pagination-template-nopagesize';
        } else {
            return '#ops-pagination-template';
        }
    },

    templateHelpers: {

        // when running on patentview.elmyra.de, let's lock down to viewer-only mode
        viewer_lockdown: function() {
            return $.url(window.location.href).attr('host') == 'patentview.elmyra.de';
        },
    },

    setup_ui: function() {

        console.log('PaginationView.setup_ui');

        var _this = this;

        var datasource = this.model.get('datasource');
        var pagesize_choices = this.model.get('pagination_pagesize_choices');
        var page_size = this.model.get('page_size');
        var result_count = this.model.get('result_count');
        var page_count_max = this.model.get('pagination_entry_count');
        var result_range = this.model.get('result_range');

        // compute number of pagination entries
        var page_count = 0;
        if (result_count > 0 && page_size > 0) {
            var need_pages = result_count / page_size;
            if (need_pages >= 1) {
                page_count = Math.ceil(need_pages);
            }
            page_count = _.min([page_count, page_count_max]);
        }

        if (page_count < 1) {
            $('.page-size-chooser').parent().remove();
            return;
        }

        // pager: create page size chooser
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

        // pager: make links from page size chooser entries
        $(this.el).find('.page-size-chooser a').click(function() {
            var value = $(this).data('value');
            _this.model.set('page_size', value);
            opsChooserApp.perform_search();
            return false;
        });

        // pager: create pagination entries
        $(this.el).find('.pagination ul').each(function(i, pagination) {
            $(this).empty();
            var self = this;
            _.range(1, page_count * page_size, page_size).map(function(index) {
                var offset = index * page_size;
                var range_begin = index;
                var range_end = range_begin + page_size - 1;
                var range = range_begin + '-' + range_end;
                var entry = _.template('<li><a href="" range="<%= range %>"><%= range %></a></li>')({range: range});
                $(self).append(entry);
            });
        });

        // pager: make links from pagination entries
        $(this.el).find('.pagination a').click(function() {
            //var action = $(this).attr('action');
            var range = $(this).attr('range');
            opsChooserApp.perform_search({range: range});
            return false;
        });

        // pager: mark proper pagination entry as active
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

});
