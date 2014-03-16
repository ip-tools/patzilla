// -*- coding: utf-8 -*-
// (c) 2013,2014 Andreas Motl, Elmyra UG

BasketModel = Backbone.Model.extend({

    defaults: {
        numberlist: [],
        ship_url: '',
        ship_param: 'payload',
    },

    // initialize model from url query parameters
    initialize: function() {
        console.log('BasketModel::initialize');
        var basket_option_names = ['numberlist', 'ship-url', 'ship-param'];
        var self = this;
        var url = $.url(window.location.href);
        _(basket_option_names).each(function(query_name) {
            var value = url.param(query_name);
            var attribute_name = query_name.replace('-', '_');
            if (value) {
                value = decodeURIComponent(value);
                value = value.split(',');
                self.set(attribute_name, value);
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
        numberlist.pop(item);
        this.trigger('change', this);
        this.trigger('change:remove', item);
    },

});

BasketView = Backbone.Marionette.ItemView.extend({

    template: "#basket-template",

    initialize: function() {
        console.log('BasketView::initialize');
        this.listenTo(this.model, "change", this.render);
        this.listenTo(this, "item:rendered", this.setup);
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

    setup: function() {
        //console.log('BasketView::setup');

        // application action: search from basket content
        $('#basket-review-button').click(function() {
            // compute cql query from numberlist in basket
            var basket = $('#basket').val();
            var query = basket
                .split('\n')
                .filter(function(entry) { return entry; })
                .map(function(entry) { return 'pn=' + entry; }).join(' OR ');
            if (query) {
                $('#query').val(query);

                // FIXME: decouple from referencing the main application object by using events!?
                opsChooserApp.perform_search();
            }
        });
    },

    onDomRefresh: function() {
        console.log('BasketView::onDomRefresh');
    },

});
