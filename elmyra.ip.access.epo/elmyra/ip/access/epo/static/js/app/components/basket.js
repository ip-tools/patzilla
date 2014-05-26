// -*- coding: utf-8 -*-
// (c) 2013,2014 Andreas Motl, Elmyra UG

BasketModel = Backbone.RelationalModel.extend({

    sync: Backbone.localforage.sync('Basket'),

    defaults: {
        numberlist: [],
        ship_url: '',
        ship_param: 'payload',
    },

    initialize: function() {
        console.log('BasketModel.initialize');
        this.init_from_query();
    },

    // initialize model from url query parameters
    init_from_query: function() {
        var basket_option_names = ['numberlist', 'ship-url', 'ship-param'];
        var _this = this;
        var url = $.url(window.location.href);
        _(basket_option_names).each(function(query_name) {
            var attribute_name = query_name.replace('-', '_');
            var value = url.param(query_name);
            // fall back to deprecated parameter name for backwards compatibility
            if (!value) {
                value = url.param(attribute_name);
            }
            if (value) {
                value = decodeURIComponent(value);
                value = value.split(',');
                _this.set(attribute_name, value);
            }
        });

    },

    // add item to basket
    add: function(item) {
        var numberlist = this.get('numberlist');
        if (_(numberlist).contains(item)) { return; }
        numberlist.push(item);
        this.trigger('change', this);
        this.trigger('change:add', item);
    },

    // remove item from basket
    remove: function(item) {
        var numberlist = this.get('numberlist');
        if (!_(numberlist).contains(item)) { return; }
        this.set('numberlist', _.without(numberlist, item));
        this.trigger('change', this);
        this.trigger('change:remove', item);
    },

    review: function(options) {

        // compute cql query from numberlist in basket
        var basket = $('#basket').val();
        if (!basket) {
            return;
        }

        var options = options || {};
        var query = null;
        var publication_numbers = basket
            .split('\n')
            .filter(function(entry) { return entry; });
        var hits = publication_numbers.length;

        // TODO: decouple from referencing the main application object e.g. by using events!?
        opsChooserApp.set_datasource('review');
        opsChooserApp.metadata.set('reviewmode', true);
        opsChooserApp.perform_listsearch(options, query, publication_numbers, hits, 'pn', 'OR');
    }

});

BasketView = Backbone.Marionette.ItemView.extend({

    template: "#basket-template",

    initialize: function() {
        console.log('BasketView.initialize');
        this.listenTo(this.model, "change", this.render);
        this.listenTo(this, "item:rendered", this.setup_ui);
    },

    serializeData: function() {
        var data = {};
        data = this.model.toJSON();

        var numberlist = this.model.get('numberlist');
        if (numberlist) {
            data['numberlist'] = numberlist.join('\n');
        }

        return data;
    },

    setup_ui: function() {
        console.log('BasketView.setup_ui');

        var _this = this;

        // basket import
        $('#basket-import-button').click(function(e) {
            _this.future_premium_feature();
            return false;
        });

        // only enable submit button, if ship url is given
        var ship_url = this.model.get('ship_url');
        if (ship_url) {
            $('#basket-submit-button').prop('disabled', false);
        } else {
            $('#basket-submit-button').prop('disabled', true);
        }

        // review feature: trigger search from basket content
        $('.basket-review-button').click(function() {
            _this.model.review();
        });

        // basket sharing
        $('#share-numberlist-email').click(function() {
            _this.future_premium_feature();
        });
        $('#share-documents-transfer').click(function() {
            _this.future_premium_feature();
        });

    },

    future_premium_feature: function() {
        bootbox.dialog(
            'Available soon via subscription.', [{
                "label": 'OK',
                "icon" : 'OK',
                "callback": null,
            }],
            {header: 'Future feature'});
    },

    onDomRefresh: function() {
        console.log('BasketView.onDomRefresh');
    },

});
