// -*- coding: utf-8 -*-
// (c) 2014 Andreas Motl, Elmyra UG

UiController = Marionette.Controller.extend({

    initialize: function() {
        log('UiController.initialize');
    },

    setup_ui: function() {

        var _this = this;

        // ------------------------------------------
        //   generic
        // ------------------------------------------

        // apply popovers to all desired buttons
        $('.btn-popover').popover();

        this.setup_text_tools();

        // defaults for notification popups
        $.notify.defaults({className: 'info', showAnimation: 'fadeIn', hideAnimation: 'fadeOut', autoHideDelay: 4000, showDuration: 300});

        // logout button
        if (opsChooserApp.config.get('mode') == 'liveview') {
            $('.logout-button').hide();
        }

        // switch query interface flavor to expert mode when receiving query via url
        if (opsChooserApp.config.get('query')) {
            opsChooserApp.queryBuilderView.set_flavor('cql');
        }


        // ------------------------------------------
        //   cql query area
        // ------------------------------------------

        // set cursor to end of query string, also focuses element
        //$('#query').caret($('#query').val().length);


        // ------------------------------------------
        //   online help
        // ------------------------------------------

        // Open help in modal dialog
        $('.action-online-help').unbind('click');
        $('.action-online-help').on('click', function() {

            // v1: modal dialog
            //$('#help-modal').modal('show');

            // v2: different page
            var baseurl = opsChooserApp.config.get('baseurl');
            var url = baseurl + '/help';
            $(this).attr('href', url);
        });


        $('.action-fullscreen').unbind('click');
        $('.action-fullscreen').click(function() {
            if (screenfull.enabled) {
                screenfull.request();
            }
        });


        $('.report-issue-feature').unbind('click');
        $('.report-issue-feature').click(function(event) {
            opsChooserApp.issues.dialog({
                element: this,
                event: event,
                what: 'feature',
                remark: 'It would be cool, if ...',
                // TODO: What about other targets like "log:error", "log:warning", "human:support", "human:user"?
                targets: 'human',
            });
        });

    },

    setup_text_tools: function() {
        // auto-shorten some texts
        $(".very-short").shorten({showChars: 5, moreText: 'more', lessText: 'less'});
    },

    reset_content: function(options) {
        options = options || {};

        $('#info-area').empty();
        //$('#pagination-info').hide();

        if (!options.keep_notifications) {
            $('#alert-area').empty();
        }
        if (!options.keep_pager) {
            //$('.pager-area').hide();
        }
        if (options.documents) {
            opsChooserApp.documents.reset();
        }
    },

    indicate_activity: function(active) {
        if (active) {
            $('.idler').hide();
            $('.spinner').show();

        } else {
            $('.spinner').hide();
            $('.idler').show();
        }
    },

    propagate_backend_errors: function(xhr, options) {

        options = options || {};

        log('propagate_backend_errors');

        $('#alert-area').empty();
        try {
            var response = jQuery.parseJSON(xhr.responseText);

        // Display detailed data from XHR response
        } catch (err) {

            console.error('Problem while propagating backend alerts:', err);

            // If decoding from JSON fails, make up a JSON error in
            // cornice-compatible format from XHR response information
            var error = {
                'location': 'unknown',
                'name': xhr.statusText,
                'description': {
                    'content': xhr.responseText,
                    'headers': {'date': xhr.getResponseHeader('Date')},
                    'status_code': xhr.status,
                    'url': xhr.requestUrl || options.url,
                }
            };

            var response = {
                'status': 'error',
                'errors': [error],
            };

        }

        return this.propagate_cornice_errors(response);

    },

    propagate_cornice_errors: function(response) {
        log('propagate_cornice_errors');
        var _this = this;
        if (response['status'] == 'error') {
            _.each(response['errors'], function(error) {

                console.error('Backend error:', error);

                if (_.isString(error.description)) {
                    var tpl = _.template($('#cornice-error-template').html(), null, {variable: 'error'});
                    //error.description = {content: error.description};

                } else if (_.isObject(error.description)) {

                    // Flavor 1: Handle objects with error.description.content
                    // Convert simple error format to detailed error format
                    if (error.description.content) {
                        var tpl = _.template($('#backend-error-template').html());
                        error.description = error.description || {};
                        _(error.description).defaults({headers: {}});

                    // Flavor 2: Handle objects with error.description.details
                    // Unwrap rich description
                    } else {
                        var tpl = _.template($('#cornice-error-template').html(), null, {variable: 'error'});
                        error.details = error.description.details;
                        error.description = error.description.user;

                    }

                }

                // Build error content and display in alert box
                var alert_html = tpl(error);
                $('#alert-area').append(alert_html);

                // Display text/html error responses from OPS inside iframe
                var html_error = $('#error-iframe').text();
                if (html_error) {
                    if (_.string.contains(html_error, 'OPS')) {
                        var base_href = '<base href="https://ops.epo.org/" />';
                        html_error = html_error.replace('<head>', '<head>' + base_href);
                    }
                    _this.iframe_write('error-iframe', html_error);
                }

            });
            $('.very-short').shorten({showChars: 0, moreText: 'more', lessText: 'less'});
            return true;
        }
        return false;
    },

    iframe_write: function(element_id, content) {
        var iframe = document.getElementById(element_id);
        iframe = iframe.contentWindow || (iframe.contentDocument.document || iframe.contentDocument);
        iframe.document.open();
        iframe.document.write(content);
        iframe.document.close();
    },

    no_results_alert: function(search_info) {
        var query_display = search_info.query;
        var query_dialog  = search_info.query;
        if (search_info.flavor == 'comfort' &&
            _.isObject(search_info.query_data) && _.isObject(search_info.query_data.criteria)) {
            query_display = JSON.stringify(search_info.query_data.criteria);
            query_dialog  = htmlentities(query_display);
        }
        if (search_info.datasource == 'ftpro' && search_info.flavor == 'cql') {
            query_display = htmlentities(search_info.query);
            query_dialog  = '&#13;' + htmlentities(search_info.query);
        }

        //search_info.query_display = htmlentities(query_display);
        search_info.query_display = query_display;
        search_info.query_dialog  = query_dialog;
        var msg = _.template($('#no-results').html(), null, {variable: 'data'})(search_info);
        this.user_alert(msg, 'warning');
    },

    do_element_visibility: function() {

        // hide all navigational- and action-elements when in print mode
        var MODE_PRINT = opsChooserApp.config.get('mode') == 'print';
        if (MODE_PRINT) {
            $('.do-not-print').hide();
        }

        // hide all navigational- and action-elements when in view-only mode
        var MODE_LIVEVIEW = opsChooserApp.config.get('mode') == 'liveview';
        if (MODE_LIVEVIEW) {
            $('.non-liveview').hide();
        }
    },

    do_elements_focus: function() {
        if (opsChooserApp.documents.length) {
            $('#patentnumber').blur();
            $('#query').blur();
        }
    },

    confirm: function(message) {
        var deferred = $.Deferred();

        var dialog = bootbox.confirm('<h4>' + message + '</h4>', function(ack) {
            if (ack) {
                deferred.resolve();
            }
        });

        // style: danger, error
        dialog.css({
            'color': '#b94a48',
            'background-color': '#f2dede',
            'border-color': '#eed3d7',
        });

        return deferred.promise();
    },

    user_alert: function(message, kind, selector) {

        if (!message) {
            return;
        }

        var label = 'INFO';
        var clazz = 'alert-info';
        if (kind == 'success') {
            label = 'SUCCESS';
            clazz = 'alert-success';

        } else if (kind == 'warning') {
            label = 'WARNING';
            clazz = 'alert-warning';

        } else if (kind == 'error') {
            label = 'ERROR';
            clazz = 'alert-danger';

        }

        var tpl = _.template($('#alert-template').html());
        var error = {
            'title': label,
            'description': message,
            'clazz': clazz,
        };
        var alert_html = tpl(error);

        selector = selector || '#info-area';
        $(selector).append(alert_html);
    },

    notify: function(message, options) {

        options = options || {};
        options.wrapper = options.wrapper || document.body;

        if (options.icon) {
            message = '<span class="icon ' + options.icon + ' icon-large"></span>' + '<p>' + message + '</p>';
        }
        if (!options.type) {
            options.type = 'notice';
        }

        if (this.notification) {
            this.notification.dismiss();
        }

        //setTimeout( function() {

            // create the notification
            this.notification = new NotificationFx({
                message : message,
                layout : 'attached',
                effect : 'bouncyflip',
                //layout : 'box',
                //effect : 'flip',
                type :   options.type, // notice, warning, error, success
                wrapper: options.wrapper,
                onClose : function() {
                    //bttn.disabled = false;
                },
                //ttl: 100000,
            });

            if (options.right) {
                this.notification.ntf.className = this.notification.ntf.className.replace('ns-attached', 'ns-attached-right');
            }

            // show the notification
            this.notification.show();

        //}, 1200 );

    },

    // perform animated scrolling
    scroll_smooth: function(target) {
        if (!target) return;
        if ($(target).offset()) {
            $('html, body').animate({
                scrollTop: $(target).offset().top
            }, 500);
        }
    },

    scroll_to_document: function(document_number) {
        var selector = 'div[data-document-number="' + document_number + '"]';
        this.scroll_smooth(selector);
    },

    copy_to_clipboard: function(mimetype, payload, options) {
        options = options || {};
        var deferred = $.Deferred();

        if (ZeroClipboard.isFlashUnusable()) {
            $(options.element).unbind('click');
            $(options.element).bind('click', function() {
                var message =
                    'Copying data to clipboard not possible, Adobe Flash Player plugin is required.<br/>' +
                    '<a href="https://get.adobe.com/flashplayer/" target="_blank">Install Adobe Flash Player</a>.';
                _ui.notify(message, {type: 'warning', icon: 'icon-copy', wrapper: options.wrapper});
            });
            return;
        }

        var zeroclipboard = new ZeroClipboard(options.element);
        zeroclipboard.on('ready', function(readyEvent) {

            // intercept the copy event to set custom data
            zeroclipboard.on('copy', function(event) {
                var clipboard = event.clipboardData;
                if (_.isFunction(payload)) {
                    payload = payload();
                }
                clipboard.setData(mimetype, payload);
            });

            // when content was copied to clipboard, notify user
            zeroclipboard.on('aftercopy', function(event) {
                // `this` === `client`
                // `event.target` === the element that was clicked
                //event.target.style.display = "none";
                if (_.isEmpty(event.data)) {
                    var message = "Empty content, nothing copied to clipboard.";
                    _ui.notify(message, {type: 'warning', icon: 'icon-copy', wrapper: options.wrapper});
                    return;
                }
                var size_value = event.data[mimetype].length;
                var size_label = 'Bytes';
                if (size_value >= 1000) {
                    var size_value = Math.round(size_value / 1000);
                    var size_label = 'kB';
                }
                var message = "Copied content to clipboard, size is " + size_value + ' ' + size_label + '.';
                _ui.notify(message, {type: 'success', icon: 'icon-copy', wrapper: options.wrapper});
            });

            deferred.resolve(zeroclipboard);

        });
        return deferred.promise();
    },

    copy_to_clipboard_bind_button: function(mimetype, payload, options) {

        // prevent default action on copy button
        $(options.element).unbind('click');
        $(options.element).click(function(e) {
            e.preventDefault();
        });

        // copy permalink to clipboard
        this.copy_to_clipboard(mimetype, payload, options);

    },

    notify_module_locked: function(modulename) {
        var message = 'The module "' + modulename + '" is not available to your account. Please subscribe to this feature.';
        this.notify(message, {type: 'warning', icon: 'icon-lock'});
    },

    open_email: function(recipient, subject, body) {
        var address_email = 'mailto:' + recipient
        var address_more = 'subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);
        var address = address_email + '?' + address_more;
        $('<iframe src="' + address + '">').appendTo('body').css('display', 'none');
    },

    open_support_email: function(subject, body) {
        this.open_email('support@elmyra.de', 'Elmyra Navigator: ' + subject, body);
    },

    pdf_icon: function() {
        return '<img src="/static/img/icons/pdf.svg" class="pdf-svg"/>';
    },

});

// setup controller
var _ui;
opsChooserApp.addInitializer(function(options) {

    this.ui = new UiController();
    _ui = this.ui;

    this.listenTo(this, 'application:ready', function() {
        this.ui.setup_ui();
    });

    this.listenTo(this, 'results:ready', function() {
        this.ui.do_elements_focus();
    });

});
