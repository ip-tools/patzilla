// -*- coding: utf-8 -*-
// (c) 2013-2015 Andreas Motl, Elmyra UG

EmbeddingController = Marionette.Controller.extend({

    initialize: function() {

        this.url = $.url(window.location.href);
        this.type = this.url.param('type');
        this.mode = this.url.param('mode');
        this.pubnumber = this.url.param('pn');

        this.hide_umbrella();
    },

    hide_umbrella: function() {
        $('.header-container').hide();
        $('#ops-pagination-region-top').hide();
        $('#ops-pagination-region-bottom').hide();
        $('.page-footer').hide();
        $('.page-footer').prev().hide();
        $('#project-chooser-area').hide();
        $('#querybuilder-basket-area').hide();
    },

    hide_regions: function() {
        opsChooserApp.queryBuilderRegion.close();
        opsChooserApp.basketRegion.close();
        opsChooserApp.metadataRegion.close();
    },

    run: function() {
        this.hide_regions();
        opsChooserApp.perform_listsearch({}, undefined, [this.pubnumber], 1, 'pn', 'OR');
    },

    process_results: function() {
        opsChooserApp.basketRegion.close();

        if (opsChooserApp.metadata.get('result_count_received') == 0) {
            opsChooserApp.ui.user_alert('No results for given criteria.', 'warning');
            return;
        }

        if (this.type == 'patent') {

        } else if (this.type == 'drawings') {

            if (this.mode == 'carousel') {

                // find drawings carousel
                var carousel = $('.drawings-carousel').parent();

                // make up carousel element as a pseudo ops-collection-entry, transfer document-number
                var document_number = carousel.closest('.ops-collection-entry').data('document-number');
                carousel.addClass('ops-collection-entry');
                carousel.attr('data-document-number', document_number);

                // massage carousel child elements
                //carousel.removeClass('span5');
                carousel.find('.drawing-info').removeClass('span12');

                $('body').html(carousel);

                opsChooserApp.document_carousel.setup_ui();

            } else {
                opsChooserApp.ui.user_alert('Unknown mode "' + this.mode + '" for type "drawings".', 'error');
                $('#ops-collection-region').hide();
            }

        } else {
            opsChooserApp.ui.user_alert('Unknown embedding type.', 'error');
            $('#ops-collection-region').hide();
        }

    },

});

$(document).ready(function() {

    console.log("document.ready");

    opsChooserApp.addInitializer(function(options) {

        this.embeddingController = new EmbeddingController();

        this.listenTo(this, 'application:ready', function() {
            this.embeddingController.run();
        });

        this.listenTo(this, 'results:ready', function() {
            this.embeddingController.process_results();
        });

    });

    opsChooserApp.start();
    boot_application();

    // Automatically run search after bootstrapping application.
    // However, from now on [2014-05-21] this gets triggered by "project:ready" events.
    // We keep this here in case we want to switch gears / provide a non-persistency
    // version of the tool for which the chance is likely, i.e. for a website embedding
    // component.
    //opsChooserApp.perform_search();

});
