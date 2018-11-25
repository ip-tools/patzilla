// -*- coding: utf-8 -*-
// (c) 2013-2018 Andreas Motl <andreas.motl@ip-tools.org>


// Widget: Modal container as Marionette region component
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


// Utility: Marionette forward-compat polyfill for `this.getOption`
(function () {

    function getOption(name) {
        return Backbone.Marionette.getOption(this, name);
    }

    Backbone.Marionette.View.getOption             =
        Backbone.Marionette.ItemView.getOption     = getOption;

})();



// Utility: Easy multiple-inheritance in Backbone.js
// https://gist.github.com/alassek/1227770
(function () {

  function extendEach () {
    var args  = Array.prototype.slice.call(arguments),
        child = this;

    _.each(args, function (proto) {
      child = child.extend(proto);
    });

    return child;
  }

  Backbone.Model.extendEach        =
    Backbone.Collection.extendEach =
    Backbone.Router.extendEach     =
    Backbone.View.extendEach       = extendEach;

  Backbone.Marionette.Controller.extendEach     =
    Backbone.Marionette.View.extendEach         =
    Backbone.Marionette.ItemView.extendEach     = extendEach;

})();


MarionetteFuture = {
    getOption: function(name) {
        return Backbone.Marionette.getOption(this, name);
    },
};


// Utlity: Directly render templates without intermediary
// `this.tagName` element, effectively using the template
// content as a replacement.
DirectRenderMixin = {

    //mode: 'wrap',
    mode: 'replace',

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
            this.$el.replaceWith(elements);
            this.setElement(elements);
        }

        this.bindUIElements();

        this.triggerMethod("render", this);
        this.triggerMethod("item:rendered", this);

        return this;
    },

};


NamedViewController = Marionette.Controller.extendEach(MarionetteFuture, {

    initialize: function(options) {
        log('NamedViewController::initialize');
        this.register_view_component();
    },

    register_view_component: function() {
        log('NamedViewController::register_view_component');
        log('name:', this.getOption('name'));
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
