// -*- coding: utf-8 -*-
// (c) 2018 Andreas Motl <andreas.motl@ip-tools.org>
'use strict';

import {View} from 'marionette';
import '@material/web/dialog/dialog.js';
import '@material/web/button/text-button.js';

export const DialogBase = View.extend({
    /*
     * Encapsulate the "Dialog" Material Web element into a Marionette View.
     *
     * https://m3.material.io/components/dialogs
     * https://material-web.dev/components/dialog/
     * https://github.com/material-components/material-web/tree/main/dialog
     *
    **/
    tagName: 'aside',

    initialize(options) {
        this.options = options || {};
        this.render();
        document.body.append(this.el);
    },

    onBeforeRender() {
        this.destroyDialog();
    },

    onRender() {
        const dialog = this.el.querySelector('md-dialog');
        const title = dialog.querySelector('[slot="headline"]');
        const content = dialog.querySelector('[slot="content"]');

        this.dialog = dialog;
        title.innerHTML = this.options.title || this.title || '';
        content.innerHTML = this.options.message || '';
        content.style.whiteSpace = 'pre-line';

        if (!title.textContent.trim()) {
            title.remove();
            dialog.ariaLabel = this.options.ariaLabel || 'Dialog';
        }

        if (this.options.confirm === false) {
            dialog.querySelector('[value="confirm"]')?.remove();
        }
        if (this.options.ok === true) {
            const close = dialog.querySelector('[value="close"]');
            if (close) close.textContent = 'OK';
        }
        if (this.options.width) {
            dialog.style.width = typeof this.options.width === 'number'
                ? `${this.options.width}px` : this.options.width;
            dialog.style.maxWidth = 'calc(100% - 48px)';
        }

        dialog.querySelectorAll('md-text-button').forEach(button => {
            button.addEventListener('click', () => {
                dialog.close(button.value);
            });
        });
    },

    onBeforeDestroy() {
        this.destroyDialog();
    },

    destroyDialog() {
        const dialog = this.dialog;
        this.dialog = undefined;
        if (dialog && this._onClosed) {
            dialog.removeEventListener('closed', this._onClosed);
        }
        this._onClosed = undefined;
        this._deferred?.reject('cancelled');
        this._deferred = undefined;
        dialog?.close();
    },

    show() {
        if (this._deferred) return this._deferred.promise();

        const dialog = this.dialog;
        const deferred = $.Deferred();
        this._deferred = deferred;
        dialog.returnValue = '';

        this._onClosed = () => {
            const confirmed = dialog.returnValue === 'confirm';
            this.destroy();

            if (confirmed) deferred.resolve();
            else deferred.reject('cancelled');
        };

        dialog.addEventListener('closed', this._onClosed, {once: true});

        dialog.show().catch(error => {
            if (this._deferred !== deferred) return;
            this.destroy();
            deferred.reject(error);
        });

        return deferred.promise();
    },
});

export const ConfirmationDialog = DialogBase.extend({
    title: 'Confirm operation',
    template: require('./dialog-confirm.html'),
});

export const SheetDialog = DialogBase.extend({
    template: require('./dialog-sheet.html'),
});
