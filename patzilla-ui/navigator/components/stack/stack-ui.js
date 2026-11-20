// -*- coding: utf-8 -*-
// (c) 2018 Andreas Motl <andreas.motl@ip-tools.org>
'use strict';

import '@material/web/menu/menu.js';
import '@material/web/menu/menu-item.js';
import '@material/web/button/outlined-button.js';

import { View } from 'marionette';
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

    It is a Material Design Web element button with dynamic content.
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
     * Encapsulate a Material Web menu in a Marionette View.
     *
     * https://m3.material.io/components/menus/overview
     * https://material-web.dev/components/menu/
     * https://github.com/material-components/material-web/tree/main/menu
     *
    **/
    tagName: 'aside',
    template: require('./stack-menu.html'),

    initialize() {
        log('StackMenuWidget::initialize', this);
        //this.listenTo(this, 'all', this.log_event);
        this.handleMenuSelection = this.handleMenuSelection.bind(this);
        this.handleMenuClosed = this.handleMenuClosed.bind(this);
        this.el.addEventListener('close-menu', this.handleMenuSelection);

        const container = this.getOption('container') || $('body');
        container.append(this.el);
        this.render();
    },

    onBeforeRender() {
        this.destroyMenu();
    },

    onRender() {
        this.menu = this.el.querySelector('md-menu');
        this.menu.anchorElement = this.getOption('anchor');
        this.menu.addEventListener('closed', this.handleMenuClosed);
    },

    onBeforeDestroy() {
        this.el.removeEventListener('close-menu', this.handleMenuSelection);
        this.destroyMenu();
    },

    destroyMenu() {
        if (!this.menu) return;

        this.menu.removeEventListener('closed', this.handleMenuClosed);
        this.menu.close();
        this.handleMenuClosed();
        this.menu = undefined;
    },

    handleMenuClosed() {
        this.getOption('anchor')?.setAttribute('aria-expanded', 'false');
    },

    handleMenuSelection(event) {
        const { initiator: item, reason } = event.detail;
        const selected = reason?.kind === 'click-selection' ||
            (reason?.kind === 'keydown' && ['Enter', 'Space'].includes(reason.key));

        if (!selected || !item?.matches('md-menu-item[data-action]') ||
            !this.menu.contains(item)) return;

        const items = Array.from(this.menu.querySelectorAll('md-menu-item'));
        const detail = { item, index: items.indexOf(item), action: item.dataset.action };
        this.trigger('item:select', detail);
        this.trigger('action:' + detail.action, detail);
    },

    open() {
        const anchor = this.getOption('anchor');
        anchor.focus();
        anchor.setAttribute('aria-expanded', 'true');
        this.menu.show();
    },
});
