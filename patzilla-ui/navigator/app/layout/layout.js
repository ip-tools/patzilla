// -*- coding: utf-8 -*-
// (c) 2013-2018 Andreas Motl <andreas.motl@ip-tools.org>
var Grid = require('split-grid').default;

LayoutView = Backbone.Marionette.Layout.extend({

    template: require('./root.html'),
    regions: {
        header: "#header-region",
        content: "#content-region",
        footer: "#footer-region",
    },

    initialize: function() {
        //log('LayoutView::initialize');
    },

    onShow: function() {

        // Select between regular vs. vendor-specific header and content variants
        var header_layout = navigatorApp.theme.get('ui.header_layout');
        var content_layout = navigatorApp.theme.get('ui.content_layout');

        if (header_layout == 'wide') {
            this.header.show(new WideHeaderView());
        } else {
            this.header.show(new HeaderView());
        }

        if (content_layout == 'grid') {
            this.content.show(new GridContentView());
        } else {
            this.content.show(new ContentView());
        }

        // Select footer view
        this.footer.show(new FooterView());
    },

    templateHelpers: {},

    onDomRefresh: function() {
        //log('LayoutView::onDomRefresh');
    },

});

ContentView = Backbone.Marionette.ItemView.extend({
    template: require('./content.html'),
    initialize: function() {
        //log('ContentView::initialize');
        this.templateHelpers.config = navigatorApp.config;
    },
    templateHelpers: {},
});

GridContentView = Backbone.Marionette.ItemView.extend({
    template: require('./content_grid.html'),
    initialize: function() {
        //log('GridContentView::initialize');
        this.templateHelpers.config = navigatorApp.config;
    },
    templateHelpers: {},
    onShow: function() {
        //log('GridContentView::onShow');

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
        //log('GridContentView::onShow grid:', grid);

    },
    onDomRefresh: function() {
        //log('GridContentView::onDomRefresh');
    },
});

MenuView = Backbone.Marionette.ItemView.extend({
    template: require('./menu.html'),
    tagName: 'span',
    initialize: function() {
        //log('MenuView::initialize');
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
        //log('HeaderView::initialize');
    },

    onShow: function() {
        //log('HeaderView::onShow');
        this.menu.show(new MenuView());
    },

    templateHelpers: function() {
        return {
            config: navigatorApp.config.attributes,
            theme: navigatorApp.theme.attributes,
        };
    },

    onRender: function() {
        //log('HeaderView::onRender');
    },

    onDomRefresh: function() {
        //log('HeaderView::onDomRefresh');
    },

});


WideHeaderView = Backbone.Marionette.Layout.extend({

    regions: {
        menu: "#menu-region",
    },

    initialize: function() {
        //log('WideHeaderView::initialize');
        this.config = this.templateHelpers.config;
        this.theme = this.templateHelpers.theme;
    },

    //template: require('./header.html'),

    template: function(model) {
        //log('WideHeaderView::template');
        var header_wide = require('./header_wide.html');
        return header_wide(model);
    },

    onShow: function() {
        //log('WideHeaderView::onShow');
        this.menu.show(new MenuView());
    },

    templateHelpers: function() {
        return {
            config: navigatorApp.config.attributes,
            theme: navigatorApp.theme.attributes,
        };
    },

    onRender: function() {
        //log('WideHeaderView::onRender');
    },

    onDomRefresh: function() {
        //log('HeaderView::onDomRefresh');
    },

});


FooterView = Backbone.Marionette.ItemView.extend({

    template: require('./footer.html'),

    initialize: function() {
        //log('FooterView::initialize');
        this.config = this.templateHelpers.config = navigatorApp.config;
    },

    templateHelpers: function() {
        return {
            config: navigatorApp.config.attributes,
            theme: navigatorApp.theme.attributes,
        };
    },

    onDomRefresh: function() {
        //log('FooterView::onDomRefresh');
    },

});
