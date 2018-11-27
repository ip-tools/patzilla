// -*- coding: utf-8 -*-
// (c) 2018 Andreas Motl <andreas.motl@ip-tools.org>
'use strict';

import { MarionetteFuture, DirectRenderMixin } from 'patzilla.lib.marionette';

export { CheckboxWidget };


// TODO: Maybe
//const CheckboxBehavior = require('marionette-checkbox-behavior');

const CheckboxWidget = Backbone.Marionette.ItemView.extendEach(MarionetteFuture, DirectRenderMixin, {
    /*
    Contemporary <input type="checkbox"> elements with bidirectional data binding.
    Derived from https://github.com/rafeememon/marionette-checkbox-behavior
    */

    template: require('./hero-checkbox.html'),

    debug: true,

    defaults: {
        inputSelector: null,
        labelSelector: null,
        modelField: null,
        textLabel: null,
    },

    // Propagate model changes to user interface
    modelEvents: function() {
        var modelEvents = {};
        modelEvents['change:' + this.getOption('modelField')] = '_updateView';
        return modelEvents;
    },

    // Propagate user interface changes to model
    events: {
        // Marionette backport
        //'change @ui.el': '_updateModel'
        'change': '_updateModel'
    },

    ui: function() {
        return {
            input: this.getOption('inputSelector'),
            label: this.getOption('labelSelector'),
        };
    },

    initialize: function() {
        this.log('CheckboxWidget::initialize');
        this.log('CheckboxWidget.model:', this.model);

        if (!this.getOption('inputSelector')) {
            throw new Error('Must specify inputSelector for CheckboxWidget');
        }
        if (!this.getOption('modelField')) {
            throw new Error('Must specify modelField for CheckboxWidget');
        }

        // https://makandracards.com/makandra/22121-how-to-call-overwritten-methods-of-parent-classes-in-backbone-js
        // https://stackoverflow.com/questions/15987490/backbone-view-inheritance-call-parent-leads-to-recursion/15988038#15988038
        CheckboxWidget.__super__.initialize.apply(this, arguments);

    },

    onRender: function() {
        this.log('CheckboxWidget::onRender');
        this._updateView();
    },

    _updateView: function() {
        this.log('CheckboxWidget::_updateView');
        var modelField = this.getOption('modelField');
        var checked = !!this.model.get(modelField);
        this.ui.input.prop('checked', checked);

        var textLabel = this.getOption('textLabel');
        this.ui.label.html(textLabel);
    },

    _updateModel: function() {
        this.log('CheckboxWidget::_updateModel');
        var modelField = this.getOption('modelField');
        //this.log('CheckboxWidget this.ui:', this.ui);
        var checked = this.ui.input.is(':checked');
        this.model.set(modelField, checked);
    },

});


//CheckboxWidget.prototype.log = Function.prototype.bind.call(console.log, console);
CheckboxWidget.prototype.log = function() {};
