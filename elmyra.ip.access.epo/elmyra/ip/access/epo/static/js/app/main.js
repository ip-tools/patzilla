ApplicationTheme = Backbone.Model.extend({

    defaults: {
        header_background_url: null,
    },

    initialize: function() {

        log('ApplicationTheme.initialize');

        // Add background image to page header at runtime, just when not being in embedded mode.
        if (!this.get('config').get('embedded')) {
            //$('.header-container').css('background-image', 'url(/static/img/header-small.jpg)');
            //this.$el.find('.header-container').css('background-image', 'url(/static/img/header-small.jpg)');
            this.set('header_background_url', '/static/img/header-small.jpg');
        }

    },
});


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

    templateHelpers: {},

    onDomRefresh: function() {
        console.log('FooterView.onDomRefresh');
    },

});
