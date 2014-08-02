// -*- coding: utf-8 -*-
// (c) 2014 Andreas Motl, Elmyra UG

ViewportPlugin = Marionette.Controller.extend({

    initialize: function(options) {
        console.log('ViewportPlugin.initialize');
        this.app = options.app;
    },

    // ux: hotkeys + and - for adding/removing the document in viewport to/from basket
    get_document_number_in_focus: function() {
        var document_in_focus = _.first($('.document-actions:in-viewport').closest('.ops-collection-entry'));
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
    },
    document_remove_basket: function() {
        var document_number = this.get_document_number_in_focus();
        if (document_number) {
            this.app.basketModel.remove(document_number);
        }
    },
    document_rate: function(score, dismiss) {
        dismiss = dismiss || false;
        var document_number = this.get_document_number_in_focus();
        return this.app.document_rate(document_number, score, dismiss);
    },

    // compute the best next list item
    next_item: function() {
        var target;
        var origin = $('.ops-collection-entry:in-viewport');
        if (origin.length) {
            var page_offset = $(window).scrollTop();
            var item_offset = Math.floor(origin.offset().top);
            if (page_offset < item_offset) {
                target = origin;
            } else {
                var target = origin.closest('.ops-collection-entry').last();
                if (target[0] === origin[0]) {
                    target = $('.ops-collection-entry:below-the-fold').first();
                }
            }

        } else {
            target = $('.ops-collection-entry:below-the-fold').first();

        }
        return target;
    },

    // compute the best previous list item
    previous_item: function() {
        var target;
        var origin = $('.ops-collection-entry:in-viewport');
        if (origin.length) {
            if ($(window).scrollTop() > origin.offset().top) {
                target = origin;
            } else {
                target = origin.closest('.ops-collection-entry').first();
                if (target[0] === origin[0]) {
                    target = $('.ops-collection-entry:above-the-top').last();
                }
                if (!target.length) {
                    target = $('body');
                }
            }
        }
        return target;
    },

});

// setup plugin
opsChooserApp.addInitializer(function(options) {
    this.viewport = new ViewportPlugin({app: this});
});
