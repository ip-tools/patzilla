// -*- coding: utf-8 -*-
// (c) 2013-2017 Andreas Motl, Elmyra UG

LayoutView = Backbone.Marionette.Layout.extend({

    template: require('./root.html'),
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
    template: require('./content.html'),
    initialize: function() {
        console.log('ContentView.initialize');
        this.templateHelpers.config = navigatorApp.config;
    },
    templateHelpers: {},
});

MenuView = Backbone.Marionette.ItemView.extend({
    template: require('./menu.html'),
    tagName: 'span',
    initialize: function() {
        console.log('MenuView.initialize');
    },
    /*
    templateHelpers: {
        component_enabled: navigatorApp.component_enabled;
    },
    */
});

HeaderView = Backbone.Marionette.Layout.extend({

    template: require('./header.html'),
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
            config: navigatorApp.config.attributes,
            theme: navigatorApp.theme.attributes,
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

    template: require('./footer.html'),

    initialize: function() {
        console.log('FooterView.initialize');
        this.config = this.templateHelpers.config = navigatorApp.config;
    },

    templateHelpers: function() {
        return {
            config: navigatorApp.config.attributes,
            theme: navigatorApp.theme.attributes,
        };
    },

    onDomRefresh: function() {
        console.log('FooterView.onDomRefresh');
    },

});
