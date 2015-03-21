// -*- coding: utf-8 -*-
// (c) 2013-2015 Andreas Motl, Elmyra UG

$(document).ready(function() {

    console.log("document.ready");

    // process and propagate application ingress parameters
    var url = $.url(window.location.href);
    var pubnumber = url.param('pn');
    //query = 'applicant=IBM';
    //query = 'publicationnumber=US2013255753A1';

    $('.page-footer').parent().hide();

    opsChooserApp.addInitializer(function(options) {

        this.listenTo(this, 'application:ready', function() {
            opsChooserApp.queryBuilderRegion.close();
            $('#project-chooser-area').hide();
            opsChooserApp.basketRegion.close();
            opsChooserApp.metadataRegion.close();
            $('#querybuilder-basket-area').hide();
            $('.header-container').hide();

            opsChooserApp.perform_listsearch({}, undefined, [pubnumber], 1, 'pn', 'OR');
        });

        this.listenTo(this, 'results:ready', function() {
            opsChooserApp.basketRegion.close();

            var carousel = $('.drawings-carousel').parent();
            //carousel.removeClass('span5');

            carousel.find('.drawing-info').removeClass('span12');

            var document_number = carousel.closest('.ops-collection-entry').data('document-number');
            log('carousel:', carousel);

            //$('body').empty();
            //$('body').append(carousel);

            carousel.addClass('ops-collection-entry');
            carousel.attr('data-document-number', document_number);

            $('body').html(carousel);

            opsChooserApp.document_carousel.setup_ui();

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
