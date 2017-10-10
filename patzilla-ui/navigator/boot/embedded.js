// -*- coding: utf-8 -*-
// (c) 2013-2016 Andreas Motl, Elmyra UG
require('./loader.js');

EmbeddingController = Marionette.Controller.extend({

    initialize: function() {

        log('Embed options:', this.options);

        this.url = $.url(window.location.href);
        log('Embed URL:', this.url);

        // Use parameters from url first
        this.type = this.url.param('type');
        this.mode = this.url.param('mode');
        this.pubnumber = this.url.param('pn');

        // Parameters from options (ex. embed_options) take precedence
        if (this.options && this.options.matchdict) {
            var field = this.options.matchdict.field;
            var value = this.options.matchdict.value;
            if (field && value) {
                if (field == 'pn') {
                    this.type = 'patent';
                    this.pubnumber = value;
                }
            }
        }

        this.hide_umbrella();
    },

    hide_umbrella: function() {
        $('.header-container').hide();
        $('#ops-pagination-region-top').hide();
        $('#ops-pagination-region-bottom').hide();
        //$('.page-footer').hide();
        //$('.page-footer').prev().hide();
        $('.footer-help').hide();
        $('#project-chooser-area').hide();
        $('#querybuilder-basket-area').hide();
    },

    hide_regions: function() {
        navigatorApp.queryBuilderRegion.close();
        navigatorApp.basketRegion.close();
        navigatorApp.metadataRegion.close();
    },

    run: function() {
        this.hide_regions();
        this.hide_umbrella();
        if (this.pubnumber) {
            navigatorApp.perform_listsearch({}, undefined, [this.pubnumber], 1, 'pn', 'OR');
        } else {
            navigatorApp.ui.user_alert('404 Not Found', 'warning');
        }
    },

    process_results: function() {
        navigatorApp.basketRegion.close();

        /*
        log('results:', navigatorApp.metadata.get('result_count_received'));
        if (!navigatorApp.metadata.get('result_count_received')) {
            navigatorApp.ui.user_alert('No results for given criteria.', 'warning');
            return;
        }
        */

        if (this.type == 'patent') {
            $('#ops-collection-region').show();

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

                navigatorApp.document_carousel.setup_ui();

            } else {
                navigatorApp.ui.user_alert('Unknown mode "' + this.mode + '" for type "drawings".', 'error');
                $('#ops-collection-region').hide();
            }

        } else {
            //navigatorApp.ui.user_alert('Unknown embed type.', 'error');
            $('#ops-collection-region').hide();
        }

    },

});

$(document).ready(function() {

    console.info("Start application [embedded]");
    navigatorApp.config.set('embedded', true);

    navigatorApp.addInitializer(function(options) {

        this.embeddingController = new EmbeddingController(options=embed_options);

        this.listenTo(this, 'application:ready', function() {
            this.embeddingController.run();
        });

        this.listenTo(this, 'results:ready', function() {
            this.embeddingController.process_results();
        });

    });

    // Transfer some options to application before booting
    if (embed_options && embed_options.params) {
        if (embed_options.params.context) {
            navigatorApp.config.set('context', embed_options.params.context);
        }
        if (embed_options.params.mode) {
            navigatorApp.config.set('mode', embed_options.params.mode);
        }
    }

    navigatorApp.start();
    navigatorApp.trigger('application:init');

    // Automatically run search after bootstrapping application.
    // However, from now on [2014-05-21] this gets triggered by "project:ready" events.
    // We keep this here in case we want to switch gears / provide a non-persistency
    // version of the tool for which the chance is likely, i.e. for a website embedding
    // component.
    //navigatorApp.perform_search();

});
