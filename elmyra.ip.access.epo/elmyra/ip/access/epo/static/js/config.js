// -*- coding: utf-8 -*-
// (c) 2014 Andreas Motl, Elmyra UG

IpsuiteNavigatorConfig = Backbone.Model.extend({

    defaults: {
        mode: undefined,
        context: 'default',
        project: 'ad-hoc',
        datasource: 'ops',
        'ship-param': 'payload',
    },

    initialize: function(options) {
        console.error('config');
        var _this = this;

        options = options || {};

        // only propagate options with defined values
        _.each(_.keys(options), function(key) {
            var value = options[key];
            if (value) {
                _this.set(key, value);
            }
        });

    },
});

ipsuiteNavigatorConfig = new IpsuiteNavigatorConfig();
