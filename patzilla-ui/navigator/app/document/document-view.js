// -*- coding: utf-8 -*-
// (c) 2013-2015 Andreas Motl, Elmyra UG
require('jquery.highlight.bartaz');
require('patzilla.navigator.util.linkmaker');
require('./util.js');

OpsExchangeDocumentView = Backbone.Marionette.Layout.extend({
    template: require('./document-view.html'),
    tagName: 'div',
    className: 'row-fluid',

    initialize: function() {
        console.log('OpsExchangeDocumentView.initialize');
    },

    // Namespace template variables to "data", also accounting for "templateHelpers".
    serializeData: function() {
        var data = this.model.attributes;
        _.extend(data, this.templateHelpers());
        return {data: data};
    },

    regions: {
        region_comment_button: '#region-comment-button',
        region_comment_text: '#region-comment-text',
    },

    onDomRefresh: function() {
        console.log('OpsExchangeDocumentView.onDomRefresh');

        // Attach current model reference to result entry dom container so it can be used by different subsystems
        // A reference to the model is required for switching between document details (biblio/fulltext)
        // and for acquiring abstracts from third party data sources.
        // In other words, this is a central gateway between the jQuery DOM world and the Backbone Marionette world.
        // However, there should be better mechanisms. Investigate! (TODO)
        var container = $(this.el).find('.ops-collection-entry');
        $(container).prop('view', this);
        $(container).prop('ops-document', this.model);

        // Swap bibliographic details with placeholder information if we encounter appropriate signal
        // TODO: Really do this onDomRefresh?
        if (this.model.get('__type__') == 'ops-placeholder') {

            // Massage LinkMaker to be suitable for use from placeholder template
            this.model.linkmaker = new Ipsuite.LinkMaker(this.model);

            // Add placeholder
            var html = require('./document-placeholder.html')({model: this.model});
            $(container).find('.ops-bibliographic-details').before(html);

            // Hide content area
            $(container).find('.ops-bibliographic-details').hide();

            // Hide other elements displaying bibliographic data
            $(container).find('.header-biblio,.document-details-chooser').hide();

        }

    },

    signalDrawingLoaded: function() {
        if (this.model.get('__type__') == 'ops-placeholder') {

            // Skip swapping in the first drawing if document has alternative representations on the same result page
            var has_alternatives = !_.isEmpty(this.model.get('alternatives_local'));
            if (has_alternatives) {
                return;
            }

            // Show content area again
            var container = $(this.el).find('.ops-collection-entry');
            $(container).find('.ops-bibliographic-details').show();

            // We don't have any bibliographic data to display, so swap to informational message
            var details = $(container).find('.ops-bibliographic-details').find('.document-details');
            var info = $('<div class="span7"></div>');
            details.replaceWith(info);

            //log('model:', this.model);
            var document_number = this.model.get_document_number();
            var message_not_available =
                'Bummer, OPS does not deliver any bibliographic data for the document "' + document_number + '" ' +
                    'and offers no alternative documents to consider.' +
                    '<br/><br/>' +
                    'However, a drawing was found in one of the upstream patent databases. ' +
                    'Please consider checking with the appropriate domestic office by selecting the ' +
                    '<a class="btn"><i class="icon-globe icon-large"></i></a> icon in the header bar of this document.' +
                    '<br/><br/>' +
                    'If the document is not available in any form which satisfies your needs, ' +
                    'do not hesitate to report this problem to us!';

            navigatorApp.ui.user_alert(message_not_available, 'info', info);
        }
    },

    events: {
        'click .rank_up img': 'rankUp',
        'click .rank_down img': 'rankDown',
        'click a.disqualify': 'disqualify',
    },

    render: function() {

        try {
            var args = Array.prototype.slice.apply(arguments);
            var result = Backbone.Marionette.Layout.prototype.render.apply(this, args);
            return result;

        } catch (error) {
            console.error('Error while rendering OpsExchangeDocumentView:', error.message, error.stack);
            var args = Array.prototype.slice.apply(arguments);
            this.model.set('error_message', error.message);
            this.template = require('./document-error.html');
            var result = Backbone.Marionette.Layout.prototype.render.apply(this, args);
            return result;
        }

    },

});

_.extend(OpsExchangeDocumentView.prototype, TemplateHelperMixin);


