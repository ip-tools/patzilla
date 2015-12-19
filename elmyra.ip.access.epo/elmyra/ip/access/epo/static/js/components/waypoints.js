// -*- coding: utf-8 -*-
// (c) 2015 Andreas Motl, Elmyra UG

WaypointController = Marionette.Controller.extend({

    initialize: function(options) {
        console.log('WaypointController.initialize');
    },

    setup_ui: function() {

        // ------------------------------------------
        //   1. trigger "document_seen"
        //   2. make header sticky
        // ------------------------------------------

        var current_header = null;

        // TODO: for letting the drawing follow the text
        /*
         $('.ops-collection-entry-heading-second').each(function() {
         var sticky = new Waypoint.Sticky({
         element: this
         });
         $(this).prop('sticky', sticky);
         });
         */
        //log('waypoint:', $('.ops-collection-entry-heading')[0]);

        Waypoint.destroyAll();

        $('.ops-collection-entry-heading').each(function() {


            //log('new Waypoint.Inview on:', this);
            var inview = new Waypoint.Inview({
                element: this,
                enter: function(direction) {
                    //log('waypoint: Enter triggered with direction ' + direction + ':', this);
                    if (direction == 'up') {

                        // TODO: for letting the drawing follow the text
                        /*
                         var container = $(this.element).closest('.ops-collection-entry')
                         var elem = container.find('.ops-collection-entry-heading-second');
                         elem.hide();
                         */

                    } else if (direction == 'down') {

                        // Feature "seen"
                        // - decrease opacity of documents marked as "seen"
                        // - mark current document as "seen" if there's no rating yet
                        var mode_seen_fade = $('#mode-seen-fade').prop('checked');
                        var document = opsChooserApp.document_base.get_document_by_element(this.element);
                        var document_number = document.get_document_number();
                        if (opsChooserApp.document_seen_twice(document_number)) {
                            if (mode_seen_fade) {
                                opsChooserApp.document_base.dim(this.element);
                            }
                        } else {
                            opsChooserApp.document_mark_seen(document_number);
                        }

                        // TODO: for letting the drawing follow the text
                        /*
                         if (current_header) {

                         var sticky = $(current_header).prop('sticky');
                         sticky.destroy();
                         current_header = null;

                         var container = $(this.element).closest('.ops-collection-entry')
                         var elem = container.find('.ops-collection-entry-heading-second');
                         setTimeout(function() {
                         var sticky = new Waypoint.Sticky({
                         element: $(elem)
                         });
                         $(elem).prop('sticky', sticky);
                         }, 100);

                         }
                         */
                    }
                },
                entered: function(direction) {
                    //log('waypoint: Entered triggered with direction ' + direction)
                },
                exit: function(direction) {
                    //log('waypoint: Exit triggered with direction ' + direction)
                },
                exited: function(direction) {
                    //log('waypoint: Exited triggered with direction ' + direction);

                    // TODO: for letting the drawing follow the text
                    /*
                     if (direction == 'down') {
                     var container = $(this.element).closest('.ops-collection-entry')
                     var elem = container.find('.ops-collection-entry-heading-second');
                     elem.show();
                     current_header = elem;

                     setTimeout(function() {
                     var sticky = new Waypoint.Sticky({
                     element: $(elem)
                     });
                     $(elem).prop('sticky', sticky);
                     }, 100);
                     }
                     */
                }
            });

        });

    },

});

// setup plugin
opsChooserApp.addInitializer(function(options) {
    this.waypoints = new WaypointController();
    this.listenTo(this, 'results:ready', function() {
        this.waypoints .setup_ui();
    });
});
