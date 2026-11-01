// -*- coding: utf-8 -*-
// (c) 2016 Andreas Motl <andreas.motl@elmyra.de>
'use strict';

export const RadioPlus = Backbone.Model.extend({

    // Machinery for rich button-based radio-/checkbox widgets

    initialize: function() {
        log('RadioPlus.initialize');
    },

    button_behaviour: function(element, event, options) {

        options = options || {};

        var $el = $(element);

        var already_active = $el.hasClass('active');
        var parent_data_toggle = $el.parent().data('toggle');

        // Prevent releasing the selection completely, if desired
        if ($el.parent().data('toggle-release') == false) {
            if (already_active) {
                event.stopPropagation();
                event.preventDefault();
                return;
            }
        }

        if (parent_data_toggle != 'buttons-radio') {
            event.stopPropagation();
        }

        // Don't toggle if data-toggle="button"
        if ($el.data('toggle') != 'button') {
            this.toggle_element($el);
        }

        // Simulate "buttons-radio" behavior, but add a third state
        if (parent_data_toggle == 'buttons-radio') {

            // Simulate third state (deactivate already pressed)
            if (already_active) {
                $el.removeClass('active');
                $el.removeClass('btn-info');
                event.stopPropagation();

            // Simulate exclusive selection (radio behavior)
            } else {
                $el.parent().find('button').attr("aria-pressed", true).addClass('btn-info').not(element).removeClass('active').removeClass('btn-info').attr("aria-pressed", false);
            }

        }

    },

    button_behaviour_bs3: function(element, is_already_active, event) {

        // Prevent releasing the selection completely, if desired
        if ($(element).parent().data('toggle-release') == false) {
            if (is_already_active) {
                event.stopPropagation();
                event.preventDefault();
                return;
            }
        }

        // Toggle radio button groups.
        if ($(element).parent().hasClass('btn-group') && $(element).find('input[type=radio]').length > 0) {
            $(element).parent().find('label').attr('aria-pressed', false).removeClass('btn-info');

            // The event will not see the new class on the clicked item, but the previous one.
            if (is_already_active) {
                $(element).removeClass('active');
                $(element).find('input').prop('checked', false);
                event.preventDefault();
                event.stopPropagation();
            } else {
                $(element).attr('aria-pressed', true).addClass('btn-info');
            }
            this.trigger('toggle');

        // Toggle single buttons or check boxes.
        } else {
            // Manually toggle state
            event.stopPropagation();
            event.preventDefault();
            $(element).toggleClass('active');

            var active = $(element).hasClass('active');
            this.toggle_element(element, active);
        }
    },

    toggle_element: function($el, state, options) {
        options = options || {};
        if (options.with_active)
            $el.toggleClass('active', state);
        $el.toggleClass('btn-info', state);
        $el.attr("aria-pressed", state);
        this.trigger('toggle');
    },

    click_handler: function($element, event, options) {
        options = options || {};
        var _this = this;

        // Control radio button behaviour.
        //_this.button_behaviour($element, event);

        var already_active = $element.hasClass('active');
        _this.button_behaviour_bs3($element, already_active, event);

        // Propagate text to label elements.
        _this.label_behaviour($element, already_active);

        // Update selection text
        _this.update_selection();

        // Toggle view-state for drill-down components
        _this.handle_drilldown();
    },

    // set label text
    label_behaviour: function(element, default_state) {

        // switch to default state
        if (default_state) {
            var active_target = $(element).data('active-target');
            var active_text   = $(active_target).data('original-text');

        // switch to state coming from selected button
        } else {
            var active_target = $(element).data('active-target');
            var active_text   = $(element).data('active-text');
        }

        // set text to appropriate element
        if (active_target && active_text) {
            $(active_target).html(active_text);
        }
    },

    get_state: function(elements) {
        elements = elements || this.get('elements');
        var modifiers = {};
        _.each(elements, function(element) {
            var name = $(element).data('name');
            var state = $(element).attr('aria-pressed') === "true";

            // handle modifier-based storage
            var modifier = $(element).data('modifier') || $(element).data('value');

            //log('state:', name, modifier, state);

            if (modifier) {
                var defaults = {};
                defaults[name] = {};
                _.defaults(modifiers, defaults);
                modifiers[name][modifier] = state;
            } else {
                modifiers[name] = state;
            }
        });
        return modifiers;
    },

    handle_drilldown: function(elements) {

        elements = elements || this.get('elements');

        // Compute button state
        var state = this.get_state(elements);

        // Iterate all elements and appropriately toggle visibility
        // for elements linked via "data-drill-down" attributes.
        _.each(elements, function(element, index) {
            var $el = $(element);

            // Get state of single element
            var name = $el.data('name');
            var value = $el.data('value');
            var element_state = state[name][value];

            // Get linked element
            var linked_element = $($el.data('drill-down'));

            // Toggle visibility
            if (linked_element) {

                if (element_state) {
                    // v1 (bs): With class "fade out hide"
                    linked_element.removeClass('hide').addClass('in');

                    // v2: jQuery-based
                    /*
                    linked_element.fadeIn('fast', function() {
                        $(this).trigger('shown');
                    });
                    */

                } else {
                    // v1 (bs): With class "fade out hide"
                    linked_element.removeClass('in').addClass('hide');

                    // v2: jQuery-based
                    //linked_element.hide();
                    //linked_element.fadeOut('fast');

                }
            }
        });

    },

    update_selection: function() {

        // Not each widget wants to display its selection.
        if (!this.get('container')) return;

        var _this = this;
        var state = this.get_state();

        var containers = this.get('container').find('.btn-group');

        _.each(containers, function(container, index) {

            var name = $(container).data('name');
            var data = _this.findKeysOfTruthyValues(state[name]);
            var labels = _this.get_selection_labels(container, name, data);
            var label_target = $(container).data('label-target');
            $(label_target).text(labels.join(', '));

        });

    },

    get_selection_labels: function(container, name, entries) {
        var labels = [];
        for (var i in entries) {
            var entry = entries[i];
            var element = $(container).find('[data-name="' + name + '"][data-value="' + entry + '"]');
            var label = element.data('label');
            labels.push(label);
        }
        return labels;
    },

    get_content_labels: function(entries, selector_prefix) {
        var labels = [];
        for (var i in entries) {
            var entry = entries[i];
            var selector = selector_prefix + '[data-value="' + entry + '"]';
            //log('selector:', selector);
            var label = $(selector).data('label');
            labels.push(label);
        }
        return labels;
    },

    findKeysOfTruthyValues: function(obj) {
        var keys = [];
        for (var key in obj) {
            var value = obj[key];
            if (value) {
                keys.push(key);
            }
        }
        return keys;
    },


});
