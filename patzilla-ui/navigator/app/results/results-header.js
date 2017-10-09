// -*- coding: utf-8 -*-
// (c) 2013-2015 Andreas Motl, Elmyra UG

MetadataView = Backbone.Marionette.ItemView.extend({
    tagName: "div",
    template: require('./results-header.html'),

    initialize: function() {
        this.templateHelpers.config = opsChooserApp.config;
        this.listenTo(this.model, "change", this.render);
        this.listenTo(this, "render", this.setup_ui);
    },

    templateHelpers: {},

    // Namespace template variables to "data", also accounting for "templateHelpers".
    serializeData: function() {
        var data = this.model.attributes;
        _.extend(data, this.templateHelpers);
        return {data: data};
    },

    setup_ui: function() {
        log('MetadataView.setup_ui');

        $('.content-chooser > button[data-toggle="tab"]').on('show', function (e) {
            // e.target // activated tab
            // e.relatedTarget // previous tab

            var list_type = $(this).data('list-type');
            if (list_type == 'ops') {
                opsChooserApp.listRegion.show(opsChooserApp.collectionView);

            } else if (list_type == 'upstream') {
                opsChooserApp.listRegion.show(opsChooserApp.resultView);
            }

        });

        opsChooserApp.trigger('metadataview:setup_ui');

    },

});


