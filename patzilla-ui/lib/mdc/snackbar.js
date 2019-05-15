// -*- coding: utf-8 -*-
// (c) 2018 Andreas Motl <andreas.motl@ip-tools.org>
'use strict';

import { classes } from 'patzilla.lib.es6';
import { MDCSnackbar } from '@material/snackbar';
import { DirectRenderMixin } from 'patzilla.lib.marionette';

export { SnackbarWidget };


class SnackbarWidget extends classes.many(Backbone.Marionette.ItemView, DirectRenderMixin) {
    /*
     * SnackbarWidget encapsulates the Snackbar Material Design Component (MDC)
     * into a `Marionette.ItemView`.
     *
     * https://material-components.github.io/material-components-web-catalog/#/component/snackbar
     *
     * Details
     * =======
     *
     * As this is intended to be instantiated only once, it will actually
     * render just once and attach itself to the HTML body on the DOM element
     * level.
     *
     * As the element is declared `aria-hidden="true"`, it will _not_ be
     * displayed on the first hand.
     *
     * When used, it will show up and disappear at runtime, which is completely
     * the responsibility of the `MDCSnackbar` controller component.
     *
    **/

    // The HTML template for a MDC Snackbar
    get template() {
        return require('./snackbar.html');
    }

    initialize() {
        this.render();
    }

    onRender() {
        this.snackbar = new MDCSnackbar(this.el);
        $("body").append(this.el);
    }

    show(message, options) {

        // Compute colors based on ambient.
        if ($('.modal-backdrop').exists()) {
            $(this.el).css('background-color', 'lightgray');
            $(this.el).find('.mdc-snackbar__text').css('color', 'black');
        } else {
            $(this.el).css('background-color', '#323232');
            $(this.el).find('.mdc-snackbar__text').css('color', 'white');
        }

        var timeout = 4000;
        if (message.length >= 30) {
            timeout = 5500;
        }
        if (message.length >= 50) {
            timeout = 7000;
        }
        this.snackbar.show({
            message: message,
            multiline: false,
            timeout: timeout,

            // https://github.com/material-components/material-components-web/issues/1398#issuecomment-391720258
            actionText: 'Dismiss',
            actionHandler: function() {},
            /*
            actionHandler: function () {
                snackbarElement.setAttribute('aria-hidden', true);
                snackbarElement.classList.remove('mdc-snackbar--active');
            }
            */
        });
    }

}
