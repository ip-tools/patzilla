// -*- coding: utf-8 -*-
// (c) 2013-2017 Andreas Motl, Elmyra UG
var Grid = require('split-grid').default;

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

        // Select between regular vs. vendor-specific header and content variants
        var vendor = navigatorApp.config.get('vendor');
        if (vendor == 'serviva') {
            this.header.show(new WideHeaderView());
            this.content.show(new GridContentView());
        } else {
            this.header.show(new HeaderView());
            this.content.show(new ContentView());
        }

        // Select footer view
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

GridContentView = Backbone.Marionette.ItemView.extend({
    template: require('./content_grid.html'),
    initialize: function() {
        console.log('GridContentView.initialize');
        this.templateHelpers.config = navigatorApp.config;
    },
    templateHelpers: {},
    onShow: function() {
        log('GridContentView.onShow');

        // Setup Grid
        // https://split.js.org/
        // https://github.com/nathancahill/split/tree/master/packages/split-grid
        var gutter = $(".gutter")[0];
        const grid = new Grid({
            columnGutters: [{
                track: 1,
                element: gutter,
            }],
        });
        log('GridContentView.grid:', grid);

    },
    onDomRefresh: function() {
        log('GridContentView.onDomRefresh');
    },
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

    regions: {
        menu: "#menu-region",
    },
    template: require('./header.html'),

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


WideHeaderView = Backbone.Marionette.Layout.extend({

    regions: {
        menu: "#menu-region",
    },

    initialize: function() {
        console.log('WideHeaderView.initialize:', this);
        this.config = this.templateHelpers.config;
        this.theme = this.templateHelpers.theme;
    },

    //template: require('./header.html'),

    template: function(model) {
        console.log('WideHeaderView.template');
        var header_wide = require('./header_wide.html');
        return header_wide(model);
    },

    onShow: function() {
        console.log('WideHeaderView.onShow');

        // TODO: Relocate to appropriate place
        //this.menu.show(new MenuView());
    },

    templateHelpers: function() {
        return {
            config: navigatorApp.config.attributes,
            theme: navigatorApp.theme.attributes,
        };
    },

    onRender: function() {
        console.log('WideHeaderView.onRender');
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
