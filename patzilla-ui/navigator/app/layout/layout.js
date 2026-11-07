// -*- coding: utf-8 -*-
// (c) 2013-2018 Andreas Motl <andreas.motl@ip-tools.org>
'use strict';

import Marionette from 'backbone.marionette';
const Grid = require('split-grid').default;

export const MainView = Marionette.View.extend({

    template: require('./root.html'),
    regions: {
        header: "#header-region",
        content: "#content-region",
        footer: "#footer-region",
    },

    initialize: function() {
        log('MainView::initialize');
    },

    onRender: function() {
        log("MainView::onRender");

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

    templateContext: {},

    onDomRefresh: function() {
        log('MainView::onDomRefresh');
    },

});

const ContentView = Marionette.View.extend({
    template: require('./content.html'),
    initialize: function() {
        //log('ContentView::initialize');
        this.templateContext.config = navigatorApp.options.config;
    },
    templateContext: {},
});

const GridContentView = Marionette.View.extend({
    template: require('./content_grid.html'),
    initialize: function() {
        //log('GridContentView::initialize');
        this.templateContext.config = navigatorApp.options.config;
    },
    templateContext: {},
    onRender: function() {
        //log('GridContentView::onRender');

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
        //log('GridContentView::onRender grid:', grid);

    },
    onDomRefresh: function() {
        //log('GridContentView::onDomRefresh');
    },
});

const MenuView = Marionette.View.extend({
    template: require('./menu.html'),
    tagName: 'span',
    initialize: function() {
        //log('MenuView::initialize');
    },
    /*
    templateContext: {
        component_enabled: navigatorApp.component_enabled;
    },
    */
});

const HeaderView = Marionette.View.extend({

    regions: {
        menu: "#menu-region",
    },
    template: require('./header.html'),

    initialize: function() {
        //log('HeaderView::initialize');
    },

    templateContext: function() {
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


const WideHeaderView = Marionette.View.extend({

    regions: {
        menu: "#menu-region",
    },

    initialize: function() {
        //log('WideHeaderView::initialize');
        this.config = this.templateContext.config;
        this.theme = this.templateContext.theme;
    },

    //template: require('./header.html'),

    template: function(model) {
        //log('WideHeaderView::template');
        var header_wide = require('./header_wide.html');
        return header_wide(model);
    },

    templateContext: function() {
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


const FooterView = Marionette.View.extend({

    template: require('./footer.html'),

    initialize: function() {
        //log('FooterView::initialize');
        this.config = this.templateContext.config = navigatorApp.options.config;
    },

    templateContext: function() {
        return {
            config: navigatorApp.config.attributes,
            theme: navigatorApp.theme.attributes,
        };
    },

    onDomRefresh: function() {
        //log('FooterView::onDomRefresh');
    },

});
