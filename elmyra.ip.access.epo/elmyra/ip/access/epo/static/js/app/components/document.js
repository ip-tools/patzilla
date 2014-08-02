// -*- coding: utf-8 -*-
// (c) 2014 Andreas Motl, Elmyra UG

DocumentDetailsController = Marionette.Controller.extend({

    initialize: function(options) {
        console.log('DocumentDetailsController.initialize');
    },

    setup_ui: function() {

        var _this = this;

        // --------------------------------------------
        //   toggle detail view (description, claims)
        // --------------------------------------------
        // TODO: refactor to ops.js
        $('button[data-toggle="tab"]').on('show', function (e) {
            // e.target // activated tab
            // e.relatedTarget // previous tab

            var content_container = $($(e.target).attr('href'));
            var details_type = $(this).data('details-type');

            var document = $(this).prop('ops-document');

            if (document) {
                var details = _this.get_details(details_type, document);
                _this.display_details(details, content_container);
            }

            // fix missing popover after switching inline detail view
            $('.btn-popover').popover();
        })

    },

    get_fulltext: function(document) {
        var clazz = OpsFulltext;
        var document_number = document.get_publication_number('epodoc');

        var country = document['@country'];
        if (country == 'DE') {
            clazz = DepatisConnectFulltext;
            document_number = document.get_publication_number('docdb');
        }

        return new clazz(document_number);
    },

    get_details: function(details_type, document) {
        var ft = this.get_fulltext(document);
        if (details_type == 'description') {
            return ft.get_description();
        } else if (details_type == 'claims') {
            return ft.get_claims();
        }
    },

    display_details: function(details, container) {
        var content_element = container.find('.document-details-content')[0];
        var language_element = container.find('.document-details-language')[0];

        if (content_element) {
            details.then(function(data) {
                if (data) {
                    $(content_element).html(data['html']);
                    data['lang'] && $(language_element).html('[' + data['lang'] + ']');
                    apply_highlighting();
                }
            });
        }

    },

});

// setup plugin
opsChooserApp.addInitializer(function(options) {
    this.document_details = new DocumentDetailsController();
    this.listenTo(this, 'results:ready', function() {
        this.document_details.setup_ui();
    });
});
