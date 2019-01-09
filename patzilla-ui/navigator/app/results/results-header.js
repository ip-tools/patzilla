// -*- coding: utf-8 -*-
// (c) 2013-2018 Andreas Motl <andreas.motl@ip-tools.org>

// TODO: Make ripple effect work.
//import {MDCRipple} from '@material/ripple';
const ripple = require('@material/ripple');


MetadataView = Backbone.Marionette.Layout.extend({
    tagName: "div",
    template: require('./results-header.html'),

    regions: {
        region_stack_opener: '#region-stack-opener',
    },

    templateHelpers: {},

    initialize: function() {
        log('MetadataView::initialize');
        this.templateHelpers.config = navigatorApp.config;
        this.listenTo(this.model, "change", this.render);
        this.listenTo(this, "render", this.setup_ui);
    },

    // Namespace template variables to "data", also accounting for "templateHelpers".
    serializeData: function() {
        var data = _.clone(this.model.attributes);
        _.extend(data, this.templateHelpers);
        return {data: data};
    },

    setup_ui: function() {
        log('MetadataView::setup_ui');

        // Display results either from OPS or from upstream
        $('.content-chooser > button[data-toggle="tab"]').on('show', function (e) {
            // e.target // activated tab
            // e.relatedTarget // previous tab

            var list_type = $(this).data('list-type');
            if (list_type == 'ops') {
                navigatorApp.listRegion.show(navigatorApp.collectionView);

            } else if (list_type == 'upstream') {
                navigatorApp.listRegion.show(navigatorApp.resultView);
            }

        });

        // Setup metadata information
        navigatorApp.trigger('metadataview:setup_ui');

        // Action: Expand all comment areas
        if (navigatorApp.component_enabled('comments')) {
            $('.action-expand-comments').off('click');
            $('.action-expand-comments').on('click', function(event) {
                navigatorApp.comments.toggle_all();
            });
        }

        // Action: Use stack mode
        if (navigatorApp.component_enabled('stack')) {
            $('.action-select-documents').off('click');
            $('.action-select-documents').on('click', function(event) {
                navigatorApp.stack.activate_all_stack();
            });

            $('.action-rate-documents').off('click');
            $('.action-rate-documents').on('click', function(event) {
                navigatorApp.stack.activate_all_rating();
            });

            // Update more user interface
            // FIXME: This just has to be done as MetadataView gets rerendered way too often!
            navigatorApp.stack.update_opener_view();

        }

    },


    onDomRefresh: function() {
        // Further UI enhancements: Material Design ripple
        /*
        $('.ripple').each(function(index, element) {
            log('ripple:', index, element);
            log('ripple:', $(element).hasClass('mdc-ripple-upgraded'));
            const rippler = new ripple.MDCRipple(element);
        });
        */
    },

});


