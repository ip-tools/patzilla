// -*- coding: utf-8 -*-
// (c) 2018 Andreas Motl <andreas.motl@ip-tools.org>
'use strict';

import {View} from 'marionette';
import { MDCSnackbar } from '@material/snackbar';

export const SnackbarWidget = View.extend({
    /*
     * SnackbarWidget encapsulates the Snackbar Material Design Component (MDC)
     * into a Marionette `View`.
     *
     * https://material-components.github.io/material-components-web-catalog/#/component/snackbar
     *
    **/
    tagName: 'aside',
    className: 'mdc-snackbar',
    template: require('./snackbar.html'),

    initialize() {
        this.render();
        document.body.append(this.el);
    },

    onBeforeRender() {
        this.destroySnackbar();
    },

    onRender() {
        this.snackbar = new MDCSnackbar(this.el);
    },

    onBeforeDestroy() {
        this.destroySnackbar();
    },

    destroySnackbar() {
        this.snackbar?.destroy();
        this.snackbar = undefined;
    },

    show(message, options) {

        // Compute colors based on ambient.
        /*
        if ($('.modal-backdrop').exists()) {
            $(this.el).css('background-color', 'lightgray');
            $(this.el).find('.mdc-snackbar__label').css('color', 'black');
        } else {
            $(this.el).css('background-color', '#323232');
            $(this.el).find('.mdc-snackbar__label').css('color', 'white');
        }
        */
        //$(this.el).css('background-color', '#323232');
        $(this.el).find('.mdc-snackbar__label,.mdc-snackbar__action').css('color', 'white');

        var timeout = 4000;
        if (message.length >= 30) {
            timeout = 5500;
        }
        if (message.length >= 50) {
            timeout = 7000;
        }
        this.snackbar.labelText = message;
        this.snackbar.timeoutMs = timeout;
        this.snackbar.actionButtonText = 'Dismiss';
        this.snackbar.open();
    },

});
