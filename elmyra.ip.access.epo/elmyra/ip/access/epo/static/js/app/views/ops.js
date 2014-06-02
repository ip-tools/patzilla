// -*- coding: utf-8 -*-
// (c) 2013,2014 Andreas Motl, Elmyra UG

OpsExchangeDocumentView = Backbone.Marionette.ItemView.extend({
    //template: "#ops-entry-template",
    template: _.template($('#ops-entry-template').html(), this.model, {variable: 'data'}),
    tagName: 'div',
    className: 'row-fluid',

    templateHelpers: {

        // date values inside publication|application-reference
        search_date: function(node) {
            var value = null;
            _.each(node, function(item) {
                if (!value && item['date'] && item['date']['$']) {
                    value = item['date']['$'];
                }
            });
            return value;
        },

        format_date: function(value) {
            if (value) {
                return value.slice(0, 4) + '-' + value.slice(4, 6) + '-' + value.slice(6, 8);
            }
        },

    },

    events: {
        'click .rank_up img': 'rankUp',
        'click .rank_down img': 'rankDown',
        'click a.disqualify': 'disqualify'
    },

    // actions to run after populating the view
    // e.g. to bind click handlers on individual records
    onDomRefresh: function() {
        var patent_number = this.model.attributes.get_patent_number();
        opsChooserApp.collectionView.basket_update_ui_entry(patent_number);
    },

});

OpsExchangeDocumentCollectionView = Backbone.Marionette.CompositeView.extend({
    tagName: "div",
    id: "opsexchangedocumentcollection",
    className: "container",
    template: "#ops-collection-template",
    itemView: OpsExchangeDocumentView,

    appendHtml: function(collectionView, itemView) {
        $(collectionView.el).append(itemView.el);
    },

    // backpropagate current basket entries into checkbox state
    // TODO: maybe refactor this elsewhere
    basket_update_ui_entry: function(entry) {
        // TODO: move to model access
        //console.log(this.model);
        var payload = $('#basket').val();
        var checkbox_element = $('#' + 'chk-patent-number-' + entry);
        var add_button_element = $('#' + 'add-patent-number-' + entry);
        var remove_button_element = $('#' + 'remove-patent-number-' + entry);
        if (_.string.include(payload, entry)) {
            checkbox_element && checkbox_element.prop('checked', true);
            add_button_element && add_button_element.hide();
            remove_button_element && remove_button_element.show();
        } else {
            checkbox_element && checkbox_element.prop('checked', false);
            add_button_element && add_button_element.show();
            remove_button_element && remove_button_element.hide();
        }
    },

});

MetadataView = Backbone.Marionette.ItemView.extend({
    tagName: "div",
    //id: "paginationview",
    template: "#ops-metadata-template",

    initialize: function() {
        this.listenTo(this.model, "change", this.render);
    },

    onDomRefresh: function() {
    },

});
