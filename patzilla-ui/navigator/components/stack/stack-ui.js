// -*- coding: utf-8 -*-
// (c) 2018 Andreas Motl <andreas.motl@ip-tools.org>
'use strict';

import { classes } from 'patzilla.lib.es6';
import { MDCMenu } from '@material/menu';
import { MarionetteFuture, DirectRenderMixin } from 'patzilla.lib.marionette';
import { CheckboxWidget } from 'patzilla.lib.hero-checkbox';

export { StackCheckboxWidget, StackOpenerWidget, StackMenuWidget };


// TODO: Maybe
//const CheckboxBehavior = require('marionette-checkbox-behavior');


// TODO: Use https://github.com/rafeememon/marionette-checkbox-behavior
const StackCheckboxWidget = CheckboxWidget.extend({
    /*
    Contemporary <input type="checkbox"> elements with bidirectional data binding.
    Derived from https://github.com/rafeememon/marionette-checkbox-behavior
    */

    inputSelector: '> input',
    labelSelector: '> .text_label',

    // Forward the "click" dom event to a "toggle" application event
    triggers: {
        //'click': 'toggle',
    },

    initialize: function() {
        //log('StackCheckboxWidget::initialize');
        // https://makandracards.com/makandra/22121-how-to-call-overwritten-methods-of-parent-classes-in-backbone-js
        // https://stackoverflow.com/questions/15987490/backbone-view-inheritance-call-parent-leads-to-recursion/15988038#15988038
        StackCheckboxWidget.__super__.initialize.apply(this, arguments);
    },

});


const StackOpenerWidget = Backbone.Marionette.ItemView.extendEach(MarionetteFuture, DirectRenderMixin, {
    /*
    Button for opening the stack user interface
    also displaying the number of selected documents.

    It is a Material Design Component (MDC) button with dynamic content.
    */

    template: require('./stack-opener.html'),

    defaults: {
    },

    // Define user interface
    ui: function() {
        return {
            count: '> #count',
        };
    },

    // Propagate model changes to user interface
    collectionEvents: {
        'sync reset': '_updateView',
        //'all': 'log_event',
    },

    // Propagate user interface events to view events
    triggers: {
        'click': 'view:clicked'
    },

    onRender: function() {
        //log('StackOpenerWidget::onRender');
        this._updateView();
    },

    get_selected_count: function() {
        var result = this.collection.where({selected: true});
        return result.length;
    },

    _updateView: function() {
        //log('StackOpenerWidget::_updateView');
        this.ui.count.html(this.get_selected_count());
    },

    log_event: function(event) {
        log('StackOpenerWidget::log_event', event);
    },

});


class StackMenuWidget extends classes.many(Backbone.Marionette.ItemView, MarionetteFuture, DirectRenderMixin) {
    /*
     * StackMenuWidget encapsulates the Menu Material Design Component (MDC)
     * into a `Marionette.ItemView`.
     *
     * https://material-components.github.io/material-components-web-catalog/#/component/menu
     *
     * Details
     * =======
     *
     * The template defines the base structure of the MDC Menu,
     * it will be appended to the DOM element obtained via the `container` option
     * when creating an instance of `StackMenuWidget`.
     *
     * Controlling the element is the responsibility of the `MDCMenu` component.
     *
    **/

    get render_once() {
        return true;
    }

    // The HTML template for a MDC Menu
    get template() {
        return require('./stack-menu.html');
    }

    initialize() {
        log('StackMenuWidget::initialize', this);
        //this.listenTo(this, 'all', this.log_event);
        this.render();
    }

    onRender() {
        //log('StackMenuWidget::onRender', this.el);
        this.setup_mdc_element();
    }

    setup_mdc_element() {
        this.$el.remove();
        this.container = this.getOption('container') || $('body');
        this.container.append(this.$el);
        this.menu = new MDCMenu(this.el);
        this.bind_mdc_events();
    }

    open() {
        //log('StackMenuWidget::open', this);
        // TODO: Sanity check to reject this when not being rendered?
        this.menu.open = true;
    }

    onClose() {
        //log('StackMenuWidget::onClose');
        this.menu.destroy();
    }


    bind_mdc_events() {
        //log('StackMenuWidget::bind_mdc_events');
        var _this = this;
        this.el.addEventListener('MDCMenu:selected', function(event) {

            //log('MDCMenu:selected', event);

            // Resolve designated action from `mdc-list-item`.
            var detail = event.detail;
            var element = $(detail.item);
            var action = element.data('action');

            // Propagate as action event
            detail.action = action;
            _this.trigger('item:select', detail);
            _this.trigger('action:' + action, detail);
        });
    }

    log_event(event) {
        log('StackMenuWidget::log_event', event);
    }

}
