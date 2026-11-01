// -*- coding: utf-8 -*-
// (c) 2013-2018 Andreas Motl <andreas.motl@ip-tools.org>
'use strict';

import Marionette from 'backbone.marionette';

// Marionette 2.4.7 uses jQuery Deferreds.
// Preserve synchronous initializer execution with jQuery 3.
// https://github.com/ip-tools/patzilla/pull/168#issuecomment-6548579723
Marionette.Callbacks.prototype.add = function(callback, contextOverride) {
    this._callbacks.push({cb: callback, ctx: contextOverride});

    this._deferred.done(function(args) {
        callback.call(contextOverride || args.context, args.options);
    });
};

// Marionette 2.4.7 relies on $el.selector, removed in jQuery 3.
// Restore the configured element so selector-based regions can re-query.
// https://github.com/ip-tools/patzilla/pull/168#discussion_r4437458622


(function() {
    var ensureElement = Marionette.Region.prototype._ensureElement;
    Marionette.Region.prototype._ensureElement = function() {
        if (!_.has(this, '_resetEl')) {
            this._resetEl = this.el;
        }
        return ensureElement.apply(this, arguments);
    };
})();

Marionette.Region.prototype.reset = function() {

    // Also support reset() before the first show().
    if (!_.has(this, '_resetEl')) {
        this._resetEl = this.getOption('el');
    }

    this.empty();

    this.el = this._resetEl;
    if (this.el instanceof Backbone.$) {
        this.el = this.el[0];
    }

    if (_.isObject(this.el)) {
        this.$el = this.getEl(this.el);
    } else {
        delete this.$el;
    }

    return this;
};

// Widget: Modal container as Marionette region component
// http://www.joezimjs.com/javascript/using-marionette-to-display-modal-views/
// see also: http://lostechies.com/derickbailey/2012/04/17/managing-a-modal-dialog-with-backbone-and-marionette/
export const ModalRegion = Marionette.Region.extend({

    constructor: function() {
        Marionette.Region.prototype.constructor.apply(this, arguments);

        // `ensureEl` longer supported with Marionette 2?
        //this.ensureEl();

        this.$el.toggleClass('fade', true);
    },

    onShow: function() {
        this.$el.modal('show');
    },

    onDestroy: function() {
        this.$el.modal('hide');
    },

});


// Utility: Propagate "extendEach" monkeypatch from Backbone to Marionette
(function () {

  Marionette.Controller.extendEach     =
    Marionette.View.extendEach         =
    Marionette.ItemView.extendEach     =
    Marionette.LayoutView.extendEach   = Backbone.Model.extendEach;

})();


export const MarionetteFuture = {
    // Modern Marionettes like to enjoy this as `this.getOption(name)`.
    // This is a forward-compat polyfill to satisfy downstream components.
    getOption: function(name) {
        return Marionette.getOption(this, name);
    },
};


export const DirectRenderMixin = {
    /*
    Utility: Directly render templates without intermediary wrapper element
    made of `this.tagName`. This effectively makes Marionette views use the
    very template content as a replacement for `this.el`.
    */

    //mode: 'wrap',
    mode: 'replace',

    // Control whether to render this only once
    renderOnce: false,

    // Bookkeeping about whether this has already been rendered
    isRendered: false,

    // How to display an item view with no tag
    // https://stackoverflow.com/questions/14659597/backbonejs-view-self-template-replacewith-and-events/49246853#49246853
    // https://stackoverflow.com/questions/11594961/backbone-not-this-el-wrapping/11598543#11598543
    render_basic: function() {
        var html = this.template();
        var el = $(html);
        this.$el.replaceWith(el);
        this.setElement(el);
        return this;
    },

    // Render the view, defaulting to underscore.js templates.
    // You can override this in your view definition to provide
    // a very specific rendering for your view. In general, though,
    // you should override the `Marionette.Renderer` object to
    // change how Marionette renders views.
    render: function() {

        // Suppress multiple rendering, if requested
        if (this.isRendered && this.renderOnce) {
            return this;
        }
        this.isRendered = true;

        //log('DirectRenderMixin::render', this);

        this.isClosed = false;

        this.triggerMethod("before:render", this);
        this.triggerMethod("item:before:render", this);

        var data = this.serializeData();
        data = this.mixinTemplateHelpers(data);

        var template = this.getTemplate();
        var html = Marionette.Renderer.render(template, data);

        // v1: Use default intermediary element to wrap content from template
        if (!this.mode || this.mode == 'wrap') {
            this.$el.html(html);

        // v2: Replace intermediary element with content from template
        } else if (this.mode == 'replace') {

            // Compute effective element(s)
            var elements = $(html);

            // Compensate for eventual non-element nodes,
            // i.e. there might be HTML remarks at the beginning of the template.
            elements = _.filter(elements, function(element) { return element.nodeType == Node.ELEMENT_NODE; });

            // Replace container element with effective elements.
            // ATTENTION: This will actually just use the first element.
            // TODO: For more elements >1, new elements could be appended to its parent node.
            this.$el.replaceWith(elements);
            this.setElement(elements);
        }

        this.bindUIElements();

        this.triggerMethod("render", this);

        return this;
    },

};


export const NamedViewController = Marionette.Controller.extendEach(MarionetteFuture, {
    /*
    In order to deduce the Marionette object currently visible in viewport,
    we needed a way to connect the DOM universe to the Marionette one.

    This helper assists by offering named helper components to be attached
    to Marionette view objects.

    The way a component is resolved by a given viewport is:

    - Calls method `this.viewport_resolver` to resolve the designated DOM element.
    - Calls method `.backboneView()` on the element, which obtains the Marionette
      view attached to the closest element having one.
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
