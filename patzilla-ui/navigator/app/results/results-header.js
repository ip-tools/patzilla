// -*- coding: utf-8 -*-
// (c) 2013-2018 Andreas Motl <andreas.motl@ip-tools.org>


MetadataView = Backbone.Marionette.ItemView.extend({
    tagName: "div",
    template: require('./results-header.html'),

    initialize: function() {
        this.templateHelpers.config = navigatorApp.config;
        this.listenTo(this.model, "change", this.render);
        this.listenTo(this, "render", this.setup_ui);
    },

    templateHelpers: {},

    // Namespace template variables to "data", also accounting for "templateHelpers".
    serializeData: function() {
        var data = _.clone(this.model.attributes);
        _.extend(data, this.templateHelpers);
        return {data: data};
    },

    setup_ui: function() {
        log('MetadataView.setup_ui');

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
                navigatorApp.comments.activate_all();
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
        }

    },

});


