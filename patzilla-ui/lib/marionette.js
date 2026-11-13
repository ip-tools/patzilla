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


export const NamedViewController = MarionetteController.extend({
    /*
    In order to deduce the Marionette object currently visible in viewport,
    we needed a way to connect the DOM universe to the Marionette one.

    This helper assists by offering named helper components to be attached
    to Marionette view objects.

    The way a component is resolved by a given viewport is:

    - Calls method `this.viewport_resolver` to resolve the designated DOM element.
    - Get the value of the object attribute called `this.name`, as this is a
      reference to the object instance of ourselves which got primarily registered
      by `this.register_view_component()`.
      When inheriting from `NamedViewController` and running through a properly
      established initializer chain, all this happens automatically.
    */

    initialize: function(options) {
        //log('NamedViewController::initialize');
        this.register_view_component();
    },

    register_view_component: function() {
        //log('NamedViewController::register_view_component');
        //log('name:', this.getOption('name'));
        var name = this.getOption('name');
        this.view[name] = this;
    },

    // @classmethod
    by_element: function(element) {
        var view = element.backboneView();
        var name = this.getOption('name');
        if (!view[name]) {
            throw new Error('No component "' + name + '" in backbone view of element');
        }
        return view[name];
    },

    // @classmethod
    by_viewport: function() {
        var name = this.getOption('name');
        var resolver = this.getOption('viewport_resolver');
        if (!resolver) {
            throw new Error('No viewport element resolver defined for  "' + name + '"');
        }
        var element = resolver.call(this);
        return this.by_element(element);
    },

});
