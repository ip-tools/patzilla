// -*- coding: utf-8 -*-
// (c) 2014 Andreas Motl, Elmyra UG

QueryBuilderView = Backbone.Marionette.ItemView.extend({

    template: "#querybuilder-template",

    initialize: function() {
        console.log('QueryBuilderView.initialize');
        //this.listenTo(this.model, "change", this.render);
        this.listenTo(this, "item:rendered", this.setup_ui);
        this.templateHelpers.config = opsChooserApp.config;
    },

    templateHelpers: {},

    setup_ui: function() {
        console.log('QueryBuilderView.setup_ui');

        var _this = this;

    },

});
