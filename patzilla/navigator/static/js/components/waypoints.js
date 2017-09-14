// -*- coding: utf-8 -*-
// (c) 2015 Andreas Motl, Elmyra UG
require('waypoints/lib/jquery.waypoints.js');
require('waypoints/lib/shortcuts/inview.js');
require('waypoints/lib/shortcuts/sticky.js');

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
        $('.ops-collection-entry-heading-second').each(function() {
            var sticky = new Waypoint.Sticky({
                element: this
            });
            $(this).prop('sticky', sticky);
        });
        log('waypoint:', $('.ops-collection-entry-heading')[0]);

        Waypoint.destroyAll();

        var _this = this;
        $('.ops-collection-entry-heading').each(function() {


            //log('new Waypoint.Inview on:', this);
            var inview = new Waypoint.Inview({
                element: this,
                enter: function(direction) {

                    var event = _this.build_event(this);
                    _this.emit_event('document:enter', event);

                    //log('waypoint: Enter triggered with direction ' + direction + ':', this);
                    if (direction == 'up') {

                        _this.emit_event('document:enter:up', event);

                        // TODO: for letting the drawing follow the text
                        /*
                         var container = $(this.element).closest('.ops-collection-entry')
                         var elem = container.find('.ops-collection-entry-heading-second');
                         elem.hide();
                         */

                    } else if (direction == 'down') {

                        _this.emit_event('document:enter:down', event);

                        // TODO: refactor to event-based
                        // Feature "seen"
                        // - decrease opacity of documents marked as "seen"
                        // - mark current document as "seen" if there's no rating yet
                        try {
                            var mode_seen_fade = opsChooserApp.project.get('mode_fade_seen');
                            if (opsChooserApp.document_seen_twice(event.document_number)) {
                                if (mode_seen_fade) {
                                    opsChooserApp.document_base.dim(this.element);
                                }
                            } else {
                                opsChooserApp.document_mark_seen(event.document_number);
                            }

                        } catch (e) {
                            log('ERROR tracking documents through waypoints:', e);
                        }

                        // TODO: for letting the drawing follow the text
                        /*
                        if (current_header) {

                            var sticky = $(current_header).prop('sticky');
                            if (sticky) {
                                sticky.destroy();
                            }
                            current_header = null;

                            var container = $(this.element).closest('.ops-collection-entry')
                            var elem = container.find('.ops-collection-entry-heading-second');
                            log('sticky elem:', elem);
                            //elem.show();
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

                    var event = _this.build_event(this);
                    _this.emit_event('document:entered', event);
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

    build_event: function(source) {

        var document = opsChooserApp.document_base.get_document_by_element(source.element);
        if (!document) return;

        var document_number = document.get_document_number();
        //log('document:', document);

        // compute current element index

        // v1: Naive, doesn't account for placeholder items, which shouldn't advance the reading progress
        //var element_index = $(source.element).parent('.ops-collection-entry').parent('.row-fluid').index();

        // v2: Count ourselves by omitting the placeholder items.
        //     In fact, it should be the even more sophisticated and should count
        //     the occurrences of _actual result items_ on the current page by having
        //     a different flavor of waypoints in place.
        //     The current ones are more user interface centric.
        //     ... but don't tell anybody (FIXME)
        var element_index = 0;
        opsChooserApp.documents.every(function(item) {
            //log('item:', item);
            if (item.attributes['__type__'] != 'ops-placeholder') {
                element_index++;
            }
            return item.attributes != document;
        });

        //log('element_index:', element_index);

        // go event-based
        var event = {
            'source': source,
            'element_index': element_index,
            'document': document,
            'document_number': document_number,
        };

        return event;

    },

    emit_event: function(name, event) {
        if (event) {
            opsChooserApp.trigger(name, event);
        }
    },

});

// setup plugin
opsChooserApp.addInitializer(function(options) {
    this.waypoints = new WaypointController();
    this.listenTo(this, 'results:ready', function() {
        this.waypoints.setup_ui();
    });
});
