// -*- coding: utf-8 -*-
// (c) 2019 Andreas Motl <andreas.motl@ip-tools.org>
'use strict';

import _ from 'underscore';
import { classes } from '../es6';

// Backbone
import { DirectRenderMixin } from '../marionette';
//import { Backbone } from 'backbone.marionette';
//require('backbone.marionette');
import Backbone from 'backbone';

// Material-UI
import React from 'react';
import ReactDOM from 'react-dom';
import FullScreenDialog from './fullscreendialog';

const log = console.log;


export class DialogWidget extends classes.many(Backbone.Marionette.ItemView, DirectRenderMixin) {

    el: any;

    render: () => void;

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
