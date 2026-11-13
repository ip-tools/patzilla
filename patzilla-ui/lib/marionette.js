// -*- coding: utf-8 -*-
// (c) 2013-2018 Andreas Motl <andreas.motl@ip-tools.org>
'use strict';

import {MnObject, Region, View, setDataApi} from "marionette";
import BackboneApi from '@mnjs/adapters/backbone';

// The Backbone adapter returns the model’s attributes for template rendering.
setDataApi(BackboneApi);


/* `Controller` was removed in Marionette v3.
 * https://github.com/marionettejs/marionette-v3-compat/blob/master/src/Controller.js
 **/
  export const MarionetteController = MnObject.extend({
    constructor(options) {
      this.options = options || {};

      const args = Array.prototype.slice.call(arguments);
      args[0] = this.options;

      //Marionette.deprecate('Marionette.Controller is deprecated. Use Marionette.Object');
      MnObject.prototype.constructor.apply(this, args);
    },

    destroy: function(...args) {
      this.triggerMethod('before:destroy', ...args);
      this.triggerMethod('destroy', ...args);
      this.stopListening();

      return this;
    }
  });


// Widget: Modal container as Marionette region component
// http://www.joezimjs.com/javascript/using-marionette-to-display-modal-views/
// see also: http://lostechies.com/derickbailey/2012/04/17/managing-a-modal-dialog-with-backbone-and-marionette/
export const ModalRegion = Region.extend({

    onBeforeShow: function() {
        $(this.el).toggleClass('fade', true);
    },

    onShow: function(region, view) {
        $(this.el).modal('show');
    },

    onDestroy: function() {
        $(this.el).modal('hide');
    },

});


// Utility: Propagate "extendEach" monkeypatch from Backbone to Marionette
(function () {

  MarionetteController.extendEach     =
              View.extendEach         = Backbone.Model.extendEach;

})();
