// -*- coding: utf-8 -*-
// (c) 2014-2018 Andreas Motl <andreas.motl@ip-tools.org>
require('patzilla.navigator.components.results-tabular');

SipResultView = ResultItemView.extend({

    //template: _.template($('#sip-entry-template').html(), this.model, {variable: 'data'}),
    template: require('./result-item.html'),

    initialize: function() {
    },

    // TODO: Maybe refactor to models/sip.js
    templateHelpers: _({}).extend(QueryLinkMixin.prototype, {

        is_application_number_invalid: function() {
            return this.cc == 'JP' && (this.ApplicationNumber.length == 7 || this.ApplicationNumber.length == 8);
        },

        get_linkable_application_number: function() {

            var number = this.cc + this.ApplicationNumber;

            // apply some massage to application numbers
            if (this.cc == 'JP' && this.kd == 'U' && this.ApplicationNumber.length < 11) {
                number = this.cc +
                    this.ApplicationNumber.substring(0, 4) +
                    _.string.rjust(this.ApplicationNumber.substring(4), 7, '0') +
                    this.kd;
            }

            return number;

        },

    }),

});
