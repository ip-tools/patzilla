// -*- coding: utf-8 -*-
// (c) 2014 Andreas Motl, Elmyra UG

FulltextProResultView = ResultItemView.extend({

    template: _.template($('#ftpro-entry-template').html(), this.model, {variable: 'data'}),

    initialize: function() {
    },

    // TODO: maybe refactor to models/ftpro.js
    templateHelpers: {

        enrich_link: function() {
            return opsChooserApp.document_base.enrich_link.apply(this, arguments);
        },

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
    },

});
