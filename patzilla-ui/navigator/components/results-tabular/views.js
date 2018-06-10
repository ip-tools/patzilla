// -*- coding: utf-8 -*-
// (c) 2014-2018 Andreas Motl <andreas.motl@ip-tools.org>

ResultItemView = Backbone.Marionette.ItemView.extend({

    tagName: 'div',
    className: 'row-fluid',

    // make additional data available in templateHelpers
    // https://stackoverflow.com/questions/12058610/backbone-marionette-templatehelpers-and-itemviewoptions/12065756#12065756
    serializeData: function() {
        var data = Backbone.Marionette.ItemView.prototype.serializeData.apply(this, arguments);
        // indicate whether result hit is missing in ops view collection
        if (!_(this.model.collection.reference_document_numbers).contains(this.model.get('publication_number')) ||
            _(this.model.collection.placeholder_document_numbers).contains(this.model.get('publication_number'))) {
            data.is_document_missing = true;
        } else {
            data.is_document_missing = false;
        }
        return data;
    },

});

ResultCollectionView = Backbone.Marionette.CompositeView.extend({

    tagName: "div",
    id: "resultcollection",
    //className: "container",
    template: _.template(''),

    getItemView: function(item) {
        log('ResultCollectionView.getItemView');
        var view_class = navigatorApp.current_datasource_info().adapter.result_item_view;
        if (view_class) {
            return view_class;
        } else {
            console.warn('Result item view not implemented for upstream provider "' + item.get('upstream_provider') + '"');
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
