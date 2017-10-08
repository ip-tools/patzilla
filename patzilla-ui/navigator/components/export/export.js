// -*- coding: utf-8 -*-
// (c) 2016 Andreas Motl, Elmyra UG
require('jquery.redirect');
var Slider = require('bootstrap-slider');
require('bootstrap-slider/dist/css/bootstrap-slider');
require('patzilla.lib.radioplus');

ExportPlugin = Backbone.Model.extend({

    initialize: function(options) {

        console.log('Initialize ExportPlugin');

        // Load dialog html from template and append to DOM
        var html = require('./export.html');
        $('body').append(html);
        this.dialog = $('#export-dialog');

        // When dialog has been attached to DOM, continue initialization
        var _this = this;
        this.dialog.ready(function() {

            // Initialize expiration time slider
            _this.ttl_element = _this.dialog.find('#expiration-time-slider');
            _this.ttl_slider = new Slider('#expiration-time-slider', {
                ticks: [1, 2, 3],
                ticks_labels: ["short", "medium", "long"],
                min: 1,
                max: 3,
                step: 1,
                value: 1,
                tooltip: 'hide',
            });

            // Initialize Radio buttons
            _this.radios = new RadioPlus({
                container: _this.dialog,
                elements: _this.dialog.find('.export-format,.export-content'),
            });
            _this.setup_dialog();

        });

    },

    setup_dialog: function() {

        var _this = this;
        var dialog = this.dialog;

        // Setup tooltips
        dialog.find('.has-tooltip').tooltip();

        // Gather form elements
        var form_elements = this.radios.get('elements');

        // Update tooltip text in dialog footer when hovering over buttons
        form_elements.unbind('mouseover').bind('mouseover', function(e) {
            _this.update_hover_text($(this));
        });


        // Handler for button selection
        form_elements.unbind('click').bind('click', function(event) {

            // Handle radio button behavior
            _this.radios.button_behaviour(this, event);

            // Update selection text
            _this.radios.update_selection(this);

            // Toggle view-state for drill-down components
            _this.radios.handle_drilldown();

        });


        // Select "All" buttons
        dialog.find('[data-toggle="select-all"]').unbind('click').bind('click', function(event) {

            // Stop event from triggering other machinery
            event.stopPropagation();
            event.preventDefault();

            // Manually toggle state
            $(this).toggleClass('active');

            // Toggle linked elements
            var active = $(this).hasClass('active');
            var target_selector = $(this).data('target');
            _this.radios.toggle_element($(this).parent().find(target_selector), active);

            // Update selection text
            _this.radios.update_selection(this);
        });


        // Setup content: Public/anonymous url
        //var ttl_element = dialog.find('#expiration-time-slider');
        _this.ttl_element.unbind('change').bind('change', function(slideEvt) {
            //var oldValue = slideEvt.value.oldValue;
            //var newValue = slideEvt.value.newValue;
            //var value = $(this).data('slider').getValue();
            //log('value:', value);

            // Update expiration time stuff after widget was acted on
            _this.update_expiration_time();
        });

        // Update expiration time stuff after widget was displayed
        $('#link-embed-content').unbind('shown').bind('shown', function() {
            _this.update_expiration_time();
        });


        // Setup input fields: Autoselect on focus
        dialog.find('#share-link-numberlist,#share-link-external').unbind('focus').bind('focus', function(event) {
            $(this).select();
        });

        // Setup "copy/paste" buttons
        var notification_wrapper = dialog[0];

        // Copy/paste links on "link-embed" screen
        opsChooserApp.ui.copy_to_clipboard('text/plain', function() {
            return dialog.find('#share-link-numberlist').val();
        }, {element: dialog.find('#share-link-numberlist-copy'), wrapper: notification_wrapper});
        opsChooserApp.ui.copy_to_clipboard('text/plain', function() {
            return dialog.find('#share-link-external').val();
        }, {element: dialog.find('#share-link-external-copy'), wrapper: notification_wrapper});

        // Copy/paste document numbers on "display" screen
        opsChooserApp.ui.copy_to_clipboard_bind_button('text/plain', function() {
            return dialog.find('#result-content-rated').val();
        }, {element: dialog.find('#result-content-rated-copy'), wrapper: notification_wrapper});
        opsChooserApp.ui.copy_to_clipboard_bind_button('text/plain', function() {
            return dialog.find('#result-content-seen').val();
        }, {element: dialog.find('#result-content-seen-copy'), wrapper: notification_wrapper});


        // Setup "open link" buttons
        dialog.find('#share-link-numberlist-open').unbind('click').bind('click', function() {
            var url = dialog.find('#share-link-numberlist').val();
            if (url) {
                open(url);
            }
        });
        dialog.find('#share-link-external-open').unbind('click').bind('click', function() {
            var url = dialog.find('#share-link-external').val();
            if (url) {
                open(url);
            }
        });


    },

    open_dialog: function(options) {

        var _this = this;
        var dialog = this.dialog;
        var basket = opsChooserApp.project.get('basket');


        // ------------------------------------------
        // Setup dialog metadata
        // ------------------------------------------
        // Add project name to dialog header
        dialog.find('#export_title').html(opsChooserApp.project.get('name'));


        // ------------------------------------------
        // Setup "link-embed" screen
        // ------------------------------------------
        // Setup content: System url
        var url = basket.get_numberlist_url();
        if (url) {
            dialog.find('#share-link-numberlist').val(url);
        } else {
            console.error('Project collection is empty or link generation failed.');
        }

        // ------------------------------------------
        // Setup "display" screen
        // ------------------------------------------
        var numbers_rated = basket.get_numbers({seen: false});
        var numbers_seen = basket.get_numbers({seen: true});
        dialog.find('#result-count-rated').html('#' + numbers_rated.length);
        dialog.find('#result-count-seen').html('#' + numbers_seen.length);
        dialog.find('#result-content-rated').val(numbers_rated.join('\n'));
        dialog.find('#result-content-seen').val(numbers_seen.join('\n'));


        // ------------------------------------------
        // Setup submit button
        // ------------------------------------------
        dialog.find('#export-dialog-send-button').show();
        dialog.find('#export-dialog-send-button').unbind('click');
        dialog.find('#export-dialog-send-button').bind('click', function(event) {

            options.element_spinner = dialog.find('#export-dialog-spinner');
            options.element_status  = dialog.find('#export-dialog-status');

            options.dialog = {
                what: dialog.find('#export-dialog-what').val(),
                remark: dialog.find('#export-dialog-remark').val(),
            };
            /*
            _this.submit(options).then(function() {
                dialog.find('#export-dialog-send-button').hide();
            });
            */
            _this.submit(options);
        });


        // ------------------------------------------
        // Show dialog
        // ------------------------------------------
        dialog.modal('show');

        // Prevent displaying the modal under backdrop
        // https://weblog.west-wind.com/posts/2016/Sep/14/Bootstrap-Modal-Dialog-showing-under-Modal-Background
        dialog.appendTo("body");

        dialog.find('#export-dialog-status').empty();

    },

    update_hover_text: function($el) {
        var action_text = $el.data('action-text');
        this.update_status(action_text);
    },

    update_status: function(text, success, failure) {
        var status_element = $('#export-dialog-action-text');
        status_element.removeClass('text-error').removeClass('text-success');
        if (success) {
            status_element.addClass('text-success');
        }
        if (failure) {
            status_element.addClass('text-error');
        }
        status_element.html(text);
    },

    get_expiration_time: function() {
        //var slider_val = this.dialog.find('#expiration-time-slider').data('slider').getValue();
        var slider_val = this.ttl_slider.getValue();
        //log('slider_val:', slider_val);
        var now = moment();
        var kmap = {
            'd': moment().add(1, 'days'),
            '1': moment().add(7, 'days'),
            '2': moment().add(30, 'days'),
            '3': moment().add(0.5, 'years'),
        };
        var exp = kmap[slider_val] || kmap['d'];
        //log('exp:', exp);
        return exp;
    },

    update_expiration_time: function() {

        //log('============ update_expiration_time');

        // Relayout slider widget
        //this.dialog.find('#expiration-time-slider').slider('relayout');
        this.ttl_slider.relayout();

        var expiration = this.get_expiration_time();
        var when = expiration.fromNow();
        this.dialog.find('#expiration-time-human').html(when);

        var expiration = parseInt(this.get_expiration_time().diff(moment()) / 1000);
        //log('expiration:', expiration);

        var basket = opsChooserApp.project.get('basket');
        var _this = this;
        basket.get_numberlist_url_liveview(expiration).then(function(url) {
            if (url) {
                _this.dialog.find('#share-link-external').val(url);
            } else {
                console.error('Project collection is empty or link generation failed.');
            }
        });

    },

    submit: function(options) {

        var _this = this;
        var element = options.element;

        var spinner = $(options.element_spinner);
        var status_text = $(options.element_status);
        spinner.show();

        var state = this.radios.get_state();

        if (_.any(state.format)) {
            var format = _.invert(state.format)[true];
            if (_(['csv', 'xlsx', 'pdf', 'zip']).contains(format)) {
                if (format == 'zip' && !_.any(state.report) && !_.any(state.media)) {
                    spinner.hide();
                    _this.update_status('Please choose any report or media format.', false, true);
                    return;
                }
                $.when(_this.export_dossier(format, {report: state.report, media: state.media})).then(function() {
                    spinner.hide();
                    _this.update_status('Data export requested.', true);
                }).fail(function() {
                    spinner.hide();
                    _this.update_status('Data export failed.', false, true);
                });
            } else if (state.format.link_embed) {
                spinner.hide();
                _this.update_status('Please use the HTTP URLs displayed above.', false, true);
            } else {
                spinner.hide();
                _this.update_status('Output format "' + format + '" not implemented yet.', false, true);
            }
        } else {
            spinner.hide();
            _this.update_status('Please select output format.', false, true);
        }

    },

    export_dossier: function(format, options) {
        options = options || {};
        var deferred = $.Deferred();
        this.get_dossier_data().then(function(dossier) {
            dossier.options = options;
            log('dossier:', dossier);
            var url = _.template('/api/util/export/dossier.<%= format %>')({ format: format});
            $.redirect(url, { json: JSON.stringify(dossier) }, 'POST', '_blank');
            deferred.resolve();
        }).fail(function() {
            deferred.reject();
        });
        return deferred.promise();
    },

    get_dossier_data: function() {

        var deferred = $.Deferred();

        var user = opsChooserApp.config.get('user');
        var project = opsChooserApp.project;
        var basket = project.get('basket');

        var seen = basket.get_records({seen: true});
        var rated = basket.get_records({seen: false, dismiss: false});
        var dismissed = basket.get_records({seen: false, dismiss: true});

        var projectname = project.get('name');
        var comments = project.get_comments().toJSON();

        $.when(project.get_queries()).then(function(queries) {
            var dossier = {
                user: user,
                name: projectname,
                project: project.toJSON(),
                queries: queries,
                collections: {
                    rated: rated,
                    dismissed: dismissed,
                    seen: seen,
                },
                comments: comments,
            };
            deferred.resolve(dossier);
        });

        return deferred.promise();
    },

});

opsChooserApp.addInitializer(function(options) {

    this.exporter = new ExportPlugin();
    this.register_component('export');

    /*
    this.listenTo(this, 'basket:activated', function(basket) {
        this.exporter.setup_ui();
    });
    */

});
