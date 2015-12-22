// -*- coding: utf-8 -*-
// (c) 2015 Andreas Motl, Elmyra UG

ReadingController = Marionette.Controller.extend({

    initialize: function(options) {
        console.log('ReadingController.initialize');

        var progressbar_options = {
            id: 'top-progress-bar',
            color: '#F44336',
            height: '2px',
            duration: 0.2
        }

        this.progressbar = new ToProgress(progressbar_options);
        this.listenTo(opsChooserApp, 'document:entered', this.enter_document);
    },

    setup_ui: function() {
        // initial progress bar update for each result page
        this.update_progress(0);
    },

    enter_document: function(event) {
        //log('enter_document:', event);
        this.update_progress(event.element_index);
    },

    update_progress: function(item_page_index) {

        var metadata = opsChooserApp.metadata;
        //log('metadata:', metadata);

        var result_count = metadata.get('result_count');
        var page_number  = metadata.get('pagination_current_page');
        var page_size    = metadata.get('page_size');

        // v1: naive
        var element_index = item_page_index;

        // v2: more sophisticated - didn't work out!
        //var element_in_viewport = opsChooserApp.viewport.get_document();
        //var element_index = element_in_viewport.parent('.row-fluid').index();

        //log('element_index:', element_index);

        //log('result_count:', result_count);

        var telemetry_valid =
            (result_count != null && result_count != undefined) &&
            (page_number  != null && page_number  != undefined);

        // compute ratio of current reading progress
        if (telemetry_valid) {
            var element_number = ((page_number - 1) * page_size) + element_index + 1;
            var ratio = (element_number / result_count) * 100;

            //log('element_number:', element_number);
            //log('ratio:', ratio);

            // update progress widget
            this.progressbar.setProgress(ratio);
        }
    },

});

// setup plugin
opsChooserApp.addInitializer(function(options) {
    this.reading = new ReadingController();
    this.listenTo(this, 'results:ready', function() {
        this.reading.setup_ui();
    });
});
