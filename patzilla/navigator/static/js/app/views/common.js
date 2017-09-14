// -*- coding: utf-8 -*-
// (c) 2013-2017 Andreas Motl, Elmyra UG

LayoutView = Backbone.Marionette.Layout.extend({

    template: "#app-layout-template",
    regions: {
        header: "#header-region",
        content: "#content-region",
        footer: "#footer-region",
    },

    initialize: function() {
        console.log('LayoutView.initialize');
    },

    onShow: function() {
        this.header.show(new HeaderView());
        this.content.show(new ContentView());
        this.footer.show(new FooterView());
    },

    templateHelpers: {},

    onDomRefresh: function() {
        console.log('LayoutView.onDomRefresh');
    },

});

ContentView = Backbone.Marionette.ItemView.extend({
    template: "#app-content-template",
    initialize: function() {
        console.log('ContentView.initialize');
    },
});

MenuView = Backbone.Marionette.ItemView.extend({
    template: "#app-menu-template",
    tagName: 'span',
    initialize: function() {
        console.log('MenuView.initialize');
    },
    /*
    templateHelpers: {
        component_enabled: opsChooserApp.component_enabled;
    },
    */
});

HeaderView = Backbone.Marionette.Layout.extend({

    template: '#app-header-template',
    regions: {
        menu: "#menu-region",
    },

    initialize: function() {
        console.log('HeaderView.initialize');
    },

    onShow: function() {
        console.log('HeaderView.onShow');
        this.menu.show(new MenuView());
    },

    templateHelpers: function() {
        return {
            config: opsChooserApp.config.attributes,
            theme: opsChooserApp.theme.attributes,
        };
    },

    onRender: function() {
        console.log('HeaderView.onRender');
    },

    onDomRefresh: function() {
        console.log('HeaderView.onDomRefresh');
    },

});


FooterView = Backbone.Marionette.ItemView.extend({

    template: "#app-footer-template",

    initialize: function() {
        console.log('FooterView.initialize');
        this.config = this.templateHelpers.config = opsChooserApp.config;
    },

    templateHelpers: function() {
        return {
            config: opsChooserApp.config.attributes,
            theme: opsChooserApp.theme.attributes,
        };
    },

    onDomRefresh: function() {
        console.log('FooterView.onDomRefresh');
    },

});


// http://www.joezimjs.com/javascript/using-marionette-to-display-modal-views/
// see also: http://lostechies.com/derickbailey/2012/04/17/managing-a-modal-dialog-with-backbone-and-marionette/
ModalRegion = Marionette.Region.extend({
    constructor: function() {
        Marionette.Region.prototype.constructor.apply(this, arguments);

        this.ensureEl();
        this.$el.toggleClass('fade hide', true);
        this.$el.on('hidden', {region:this}, function(event) {
            event.data.region.close();
        });
    },

    onShow: function() {
        this.$el.modal('show');
    },

    onClose: function() {
        this.$el.modal('hide');
    }
});
