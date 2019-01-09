// -*- coding: utf-8 -*-
// (c) 2014-2018 Andreas Motl <andreas.motl@ip-tools.org>
'use strict';

import { StackDisplayMode } from 'patzilla.navigator.components.stack';

require('jquery.viewport');


const ViewportPlugin = Marionette.Controller.extend({

    initialize: function(options) {
        console.log('ViewportPlugin.initialize');
        this.app = options.app;

        this.bottom_area_height = 20;
    },

    get_document: function() {
        var document_in_focus = $('.document-anchor:in-viewport').closest('.ops-collection-entry').first();
        return document_in_focus;
    },

    get_document_number_in_focus: function() {
        var document_in_focus = this.get_document();
        var document_number = $(document_in_focus).data('document-number');
        return document_number;
    },

    get_rating_widget: function(document_number) {
        return $('#rate-patent-number-' + document_number);
    },

    document_add_basket: function() {
        var document_number = this.get_document_number_in_focus();
        if (document_number) {
            this.app.basketModel.add(document_number);
        }
        this.activate_rating_widget();
    },
    document_remove_basket: function() {
        var document_number = this.get_document_number_in_focus();
        if (document_number) {
            this.app.basketModel.remove(document_number);
        }
        this.activate_rating_widget();
    },
    document_rate: function(score, dismiss) {
        this.activate_rating_widget();
        dismiss = dismiss || false;
        var document_number = this.get_document_number_in_focus();
        return this.app.document_rate(document_number, score, dismiss);
    },

    activate_rating_widget: function() {
        if (navigatorApp.component_enabled('stack')) {
            navigatorApp.stack.activate_by_viewport(StackDisplayMode.RATING);
        }
    },

    // compute the best next list item
    next_item: function(options) {
        options = options || {};

        var target;

        var origin = $('.ops-collection-entry:in-viewport');
        if (!origin.exists()) {

            // 2016-04-23: Directly turn over to next page with results
            // when hitting the "Removed family members" placeholder at the
            // end of a remote result page.
            var family_members_removed_empty_page = $('#family-members-removed-empty-page');
            if (family_members_removed_empty_page.exists()) {
                var next_page = $('#next-page-with-results-button').data('next-page');
                if (next_page) {
                    navigatorApp.paginationViewBottom.set_page(next_page);
                    return;
                }
            }

            // Otherwise, use next regular entry as scroll target
            target = $('.ops-collection-entry:below-the-fold');
            return target;
        }

        var next = origin.parent().next().find('.ops-collection-entry').first();

        var bottom_visible = $(window).scrollTop() + $(window).height() > getDocumentHeight() - this.bottom_area_height;

        var bottom_overdraw = false;

        var page_offset = $(window).scrollTop();
        var item_offset = Math.floor(origin.offset().top);
        if (page_offset < item_offset - 3) {
            target = origin;
            bottom_overdraw = bottom_visible;
        } else {
            target = next;
            bottom_overdraw = bottom_visible || !next.exists();
        }

        if (bottom_overdraw && options.paging) {
            try {
                navigatorApp.paginationViewBottom.set_page('next');
                return;
            } catch(err) {
                // FIXME: properly log error

            }
        }

        return target;
    },

    // compute the best previous list item
    previous_item: function(options) {
        options = options || {};
        var target;
        var origin = $('.ops-collection-entry:in-viewport');
        if (origin.length) {
            if ($(window).scrollTop() > origin.offset().top) {
                target = origin;
            } else {
                target = origin.closest('.ops-collection-entry').first();
                if (target[0] === origin[0]) {
                    target = $('.ops-collection-entry:above-the-top').last();
                    var top_overdraw = !target.exists();
                    if (top_overdraw && options.paging) {
                        try {
                            navigatorApp.paginationViewBottom.set_page('previous');
                        } catch(err) {
                            // FIXME: properly log error

                        }
                    }
                }
                if (!target.exists()) {
                    target = $('body');
                }
            }
        } else {

            // 2016-04-23: Directly turn over to direct previous page
            // when hitting the "Removed family members" placeholder at the
            // end of a remote result page.
            var family_members_removed_empty_page = $('#family-members-removed-empty-page');
            if (family_members_removed_empty_page.exists()) {
                navigatorApp.paginationViewBottom.set_page('previous');
                return;
            }

        }
        return target;
    },

});

// setup plugin
navigatorApp.addInitializer(function(options) {
    this.viewport = new ViewportPlugin({app: this});
});
