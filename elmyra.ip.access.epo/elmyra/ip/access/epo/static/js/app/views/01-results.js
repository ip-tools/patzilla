// -*- coding: utf-8 -*-
// (c) 2014 Andreas Motl, Elmyra UG

ResultItemView = Backbone.Marionette.ItemView.extend({

    tagName: 'div',
    className: 'row-fluid',

    // make additional data available in templateHelpers
    // https://stackoverflow.com/questions/12058610/backbone-marionette-templatehelpers-and-itemviewoptions/12065756#12065756
    serializeData: function() {
        var data = Backbone.Marionette.ItemView.prototype.serializeData.apply(this, arguments);
        // indicate whether result hit is missing in ops view collection
        data.is_document_missing = !_(this.model.collection.reference_document_numbers).contains(this.model.get('publication_number'));
        return data;
    },

});

ResultCollectionView = Backbone.Marionette.CompositeView.extend({

    tagName: "div",
    id: "resultcollection",
    className: "container",
    template: "#generic-collection-template",

    getItemView: function(item) {
        if (item.get('upstream_provider') == 'ftpro') {
            return FulltextProResultView;
        } else {
            console.error('Could not create result view instance for upstream provider "' + model.get('upstream_provider') + '"');
        }
    },

    initialize: function(options) {
        console.log('ResultCollectionView.initialize');
    },

    onRender: function() {
        console.log('ResultCollectionView.onRender');
    },

    /*
    // Override and disable add:render event, see also:
    // https://github.com/marionettejs/backbone.marionette/issues/640
    _initialEvents: function() {
        if (this.collection) {
            //this.listenTo(this.collection, "add", this.addChildView, this);
            this.listenTo(this.collection, "remove", this.removeItemView, this);
            this.listenTo(this.collection, "reset", this.render, this);
        }
    },
    */

});
