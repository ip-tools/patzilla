// -*- coding: utf-8 -*-
// (c) 2013,2014 Andreas Motl, Elmyra UG

// http://www.joezimjs.com/javascript/using-marionette-to-display-modal-views/
// see also: http://lostechies.com/derickbailey/2012/04/17/managing-a-modal-dialog-with-backbone-and-marionette/
ModalRegion = Marionette.Region.extend({

    constructor: function() {
        Marionette.Region.prototype.constructor.apply(this, arguments);

        this.ensureEl();
        this.$el.toggleClass('fade hide', true);
        this.$el.on('hidden', {region:this}, function(event) {
            event.data.region.close();
        });
    },

    onShow: function() {
        this.$el.modal('show');
    },

    onClose: function() {
        this.$el.modal('hide');
    }
});
