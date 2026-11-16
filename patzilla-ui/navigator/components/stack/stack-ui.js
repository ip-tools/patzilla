// -*- coding: utf-8 -*-
// (c) 2018 Andreas Motl <andreas.motl@ip-tools.org>
'use strict';

import { View } from 'marionette';
import { MDCMenu } from '@material/menu';
import { CheckboxWidget } from 'patzilla.lib.hero-checkbox';

// TODO: Maybe
//const CheckboxBehavior = require('marionette-checkbox-behavior');

// TODO: Use https://github.com/rafeememon/marionette-checkbox-behavior
export const StackCheckboxWidget = CheckboxWidget.extend({
    /*
    Contemporary <input type="checkbox"> elements with bidirectional data binding.
    Derived from https://github.com/rafeememon/marionette-checkbox-behavior
    */

    inputSelector: ':scope input',
    labelSelector: ':scope .text_label',

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


export const StackOpenerWidget = View.extend({
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
            count: ':scope #count',
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
        $(this.ui.count).html(this.get_selected_count());
    },

    log_event: function(event) {
        log('StackOpenerWidget::log_event', event);
    },

});


export const StackMenuWidget = View.extend({
    /*
     * StackMenuWidget encapsulates the Menu Material Design Component (MDC)
     * into a Marionette `View`.
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
    tagName: 'div',
    className: 'mdc-menu mdc-menu-surface stack-menu',
    template: require('./stack-menu.html'),

    initialize() {
        log('StackMenuWidget::initialize', this);
        //this.listenTo(this, 'all', this.log_event);
        this.handleMdcSelected = this.handleMdcSelected.bind(this);
        this.el.addEventListener('MDCMenu:selected', this.handleMdcSelected);

        this.render();
        const container = this.getOption('container') || $('body');
        container.append(this.el);
    },

    onBeforeRender() {
        this.destroyMenu();
    },

    onRender() {
        this.menu = new MDCMenu(this.el);
    },

    onBeforeDestroy() {
        this.el.removeEventListener('MDCMenu:selected', this.handleMdcSelected);
        this.destroyMenu();
    },

    destroyMenu() {
        this.menu?.destroy();
        this.menu = undefined;
    },

    handleMdcSelected(event) {
        const detail = event.detail;
        detail.action = $(detail.item).data('action');

        this.trigger('item:select', detail);
        this.trigger('action:' + detail.action, detail);
    },

    open() {
        this.menu.open = true;
    },
});
