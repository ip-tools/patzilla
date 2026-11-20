// -*- coding: utf-8 -*-
// (c) 2018 Andreas Motl <andreas.motl@ip-tools.org>
'use strict';

import {View} from 'marionette';
import '@material/web/labs/gb/components/snackbar/md-gb-snackbar.js';

export const SnackbarWidget = View.extend({
    /*
     * SnackbarWidget encapsulates the Snackbar Material Design element
     * into a Marionette `View`.
     *
     * https://m3.material.io/components/snackbar/overview
     * https://github.com/material-components/material-web/tree/main/labs/gb/components/snackbar
     *
    **/
    tagName: 'aside',
    className: 'snackbar-widget',
    template: require('./snackbar.html'),

    initialize() {
        this.render();
        document.body.append(this.el);
    },

    onBeforeRender() {
        this.destroySnackbar();
    },

    onRender() {
        this.snackbar = this.el.querySelector('md-gb-snackbar');
    },

    onBeforeDestroy() {
        this.destroySnackbar();
    },

    destroySnackbar() {
        this.snackbar?.remove();
        this.snackbar = undefined;
    },

    show(message, options) {
        // Restart the timeout when another message arrives.
        if (this.snackbar.open) {
            this.snackbar.close();
        }

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
        //$(this.el).find('.mdc-snackbar__label,.mdc-snackbar__action').css('color', 'white');

        const timeout = message.length >= 50 ? 7000
            : message.length >= 30 ? 5500
            : 4000;

        this.snackbar.labelText = message;
        this.snackbar.timeoutMs = timeout;
        this.snackbar.show();
    },
});
