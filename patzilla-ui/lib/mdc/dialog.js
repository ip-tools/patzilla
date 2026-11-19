// -*- coding: utf-8 -*-
// (c) 2018 Andreas Motl <andreas.motl@ip-tools.org>
'use strict';

import {View} from 'marionette';
import {MDCDialog} from '@material/dialog';

export const DialogBase = View.extend({
    /*
     * Encapsulate the "Dialog" Material Design Component (MDC) into a Marionette `View`.
     *
     * https://m2.material.io/components/dialogs
     * https://material-components.github.io/material-components-web-catalog/#/component/dialog
     * https://github.com/material-components/material-components-web/tree/master/packages/mdc-dialog
     *
    **/

    tagName: 'div',
    className: 'mdc-dialog',

    initialize(options) {
        this.options = options || {};
        this.render();
        document.body.append(this.el);
    },

    onBeforeRender() {
        this.destroyDialog();
    },

    onRender() {
        this.dialog = new MDCDialog(this.el);
        const surface = this.el.querySelector('.mdc-dialog__surface');
        const title = this.el.querySelector('.mdc-dialog__title');
        const content = this.el.querySelector('.mdc-dialog__content');
        const idPrefix = `mdc-dialog-${this.cid}`;

        content.innerHTML = this.options.message;
        content.style.whiteSpace = 'pre-line';
        content.id = `${idPrefix}-content`;

        title.innerHTML = this.options.title || this.title || '';

        this.el.setAttribute('role', 'dialog');
        this.el.setAttribute('aria-modal', 'true');
        this.el.setAttribute('aria-describedby', content.id);

        if (title.textContent.trim()) {
            title.id = `${idPrefix}-title`;
            this.el.setAttribute('aria-labelledby', title.id);
            this.el.removeAttribute('aria-label');
        } else {
            title.removeAttribute('id');
            this.el.removeAttribute('aria-labelledby');
            this.el.setAttribute('aria-label', this.options.ariaLabel || 'Dialog');
        }

        if (this.options.confirm === false) {
            $(this.el).find('[data-mdc-dialog-action="confirm"]').hide();
        }
        if (this.options.ok === true) {
            $(this.el).find('[data-mdc-dialog-action="close"]').find('.mdc-button__label').html('OK');
        }
        if (this.options.width) {
            $(surface).css('width', this.options.width);
        }
    },

    onBeforeDestroy() {
        this.destroyDialog();
    },

    destroyDialog() {
        this.dialog?.destroy();
        this.dialog = undefined;
    },

    show() {
        const deferred = $.Deferred();
        const _this = this;
        this.el.addEventListener('MDCDialog:closed', function(event) {
            const confirmed = event.detail.action === 'confirm';
            _this.destroyDialog();
            _this.el.remove();

            if (confirmed) {
                deferred.resolve();
            } else {
                deferred.reject('cancelled');
            }
        }, {once: true});

        this.dialog.open();
        return deferred.promise();
    },
});


export const ConfirmationDialog = DialogBase.extend({
    title: 'Confirm operation',
    template: require('./dialog-confirm.html'),
});


export const SheetDialog = DialogBase.extend({
    className: 'mdc-dialog mdc-dialog--sheet',
    template: require('./dialog-sheet.html'),
});
