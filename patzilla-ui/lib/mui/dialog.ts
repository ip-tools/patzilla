// -*- coding: utf-8 -*-
// (c) 2019 Andreas Motl <andreas.motl@ip-tools.org>
'use strict';

import _ from 'underscore';

// Marionette
import {View} from 'marionette';

// Material-UI
import React from 'react';
import ReactDOM from 'react-dom';
import FullScreenDialog from './fullscreendialog';

const log = console.log;


export class DialogWidget extends View {

    el: any;

    // The HTML template for making up a HTML element
    get template() {
        return _.template('<div></div>');
    }

    initialize() {
        log('DialogWidget.initialize');
        this.render();
    }

    onRender() {
        log('DialogWidget.onRender');

        // https://stackoverflow.com/questions/41897420/typescript-and-reactdom-render-method-doesnt-accept-component/41897800#41897800
        const dialog = React.createElement(FullScreenDialog, {open: true});
        ReactDOM.render(
            dialog,
            this.el
        );

    }

    show(message, options) {
        log('DialogWidget');
    }

}
