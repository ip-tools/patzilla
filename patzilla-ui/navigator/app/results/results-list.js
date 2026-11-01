// -*- coding: utf-8 -*-
// (c) 2013-2015 Andreas Motl, Elmyra UG
'use strict';

const {OpsExchangeDocumentView} = require("patzilla.navigator.app.document/document-view");

export const OpsExchangeDocumentCollectionView = Marionette.CompositeView.extend({
    tagName: "div",
    id: "ops-collection-container",
    className: "",
    template: require('./results-list.html'),
    childView: OpsExchangeDocumentView,

    initialize: function(options) {
        console.log('OpsExchangeDocumentCollectionView.initialize');
    },

    // Override and disable add:render event, see also:
    // https://github.com/marionettejs/Marionette/issues/640
    _initialEvents: function() {
        if (this.collection) {
            //this.listenTo(this.collection, "add", this.addChildView, this);
            this.listenTo(this.collection, "remove", this._onCollectionRemove, this);
            this.listenTo(this.collection, "reset", this.render, this);
        }
    },

    // Override the "close" method, otherwise the events bound by "_initialEvents" would vanish
    // which leads to the view children not being re-rendered when resetting its collection.
    // See also region.show(view, {preventClose: true}) in more recent versions of Marionette.
    close: function() {
    },

    onRender: function() {
        console.log('OpsExchangeDocumentCollectionView.onRender');
    },

    onDomRefresh: function() {
        console.log('OpsExchangeDocumentCollectionView.onDomRefresh');
    },

});
