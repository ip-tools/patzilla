// -*- coding: utf-8 -*-

OpsChooserApp = new Backbone.Marionette.Application();

OpsChooserApp.addRegions({
    listRegion: "#ipdocumentcollection-region"
});

IpDocument = Backbone.Model.extend({

    defaults: {
        votes: 0,
        selected: false
    },

    select: function() {
        this.set('selected', true);
    },
    unselect: function() {
        this.set('selected', false);
    }

});

IpDocumentCollection = Backbone.Collection.extend({

    model: IpDocument,

    initialize: function(ipdocumentcollection) {
        var self = this;
    },

});

IpDocumentView = Backbone.Marionette.ItemView.extend({
    template: "#ipdocument-template",
    tagName: 'tr',
    className: 'ipdocument',

    events: {
        'click .rank_up img': 'rankUp',
        'click .rank_down img': 'rankDown',
        'click a.disqualify': 'disqualify'
    },

});

IpDocumentCollectionView = Backbone.Marionette.CompositeView.extend({
    tagName: "table",
    id: "ipdocumentcollection",
    className: "table table-bordered table-condensed table-hover",
    template: "#ipdocumentcollection-template",
    itemView: IpDocumentView,

    appendHtml: function(collectionView, itemView){
        collectionView.$("tbody#ipdocumentcollection-tbody").append(itemView.el);
    }
});

OpsChooserApp.addInitializer(function(options){
    var ipDocumentCollectionView = new IpDocumentCollectionView({
        collection: options.documents
    });
    OpsChooserApp.listRegion.show(ipDocumentCollectionView);
});

$(document).ready(function(){

    console.log("OpsChooserApp starting");

    var documents = new IpDocumentCollection([
        new IpDocument({
            patent_number: 'EP666666A1',
            publication_date: '2010-01-01',
            title: 'Some title',
            applicant: 'Some applicant',
            ipc: 'A68H'
        }),
        new IpDocument({
            patent_number: 'DE123456A1',
            publication_date: '2012-05-20',
            title: 'Another title',
            applicant: 'Another applicant',
            ipc: 'A68G'
        }),
    ]);
    documents.fetch();

    OpsChooserApp.start({documents: documents});

});
