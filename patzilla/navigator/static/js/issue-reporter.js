// -*- coding: utf-8 -*-
// (c) 2016-2017 Andreas Motl, Elmyra UG
var StackTrace = require('stacktrace-js');

IssueReporter = Backbone.Model.extend({

    defaults: {
        api_url: '/api/util/issue/report',
        targets: ['log'],
    },

    initialize: function(options) {
        console.log('Initialize IssueReporter');
    },

    setup_stacktrace_interceptor: function(options) {

        var _this = this;

        // Register global error handler
        window.onerror = function(msg, file, line, col, error) {

            // Build report object
            var report = new IssueReport({
                origin: 'javascript',
                kind:   'exception',
            });
            report.set('javascript', {
                msg: msg,
                file: file,
                line: line,
                col: col,
                stackframes: [],
            });

            // Regular stacktrace.js handler
            // https://github.com/stacktracejs/stacktrace.js
            var stacktrace_callback = function(stackframes) {

                // Serialize stackframes as strings
                var stackframes_serialized = stackframes.map(function(sf) {
                    return sf.toString();
                });
                console.log('Collecting stacktrace succeeded');

                // Add stackframes to issue report
                report.get('javascript').stackframes = stackframes_serialized;

                // Send report to backend
                _this.send(report, options);

            };

            // Fallback stacktrace.js error handler
            var stacktrace_errback = function(err) {

                console.warn('Collecting stacktrace failed');

                // Send error to Javascript console
                console.error(error);

                // Send report to backend
                _this.send(report, options);
            };


            // Register stacktrace.js handlers
            // Callback is called with an Array[StackFrame]
            console.log('Collecting stacktrace');
            StackTrace.fromError(error).then(stacktrace_callback).catch(stacktrace_errback);

        };

    },

    send: function(report, options) {

        options = options || {};

        var targets = this.get('targets');
        if (options.targets) {
            targets = targets.concat(options.targets);
        }
        //log('targets:', targets);

        var uri = this.get('api_url');
        uri += '?' + $.param({targets: targets.join(',')});

        var deferred = $.Deferred();
        $.ajax({
            method: 'post',
            url: uri,
            async: true,
            data: JSON.stringify(report.toJSON()),
            contentType: "application/json; charset=utf-8",

        }).success(function(response, status, options) {
            console.log('Successfully submitted issue report to backend');
            deferred.resolve(response, status, options);

        }).error(function(xhr, settings) {
            console.warn('Error submitting issue report to backend');
            deferred.reject(xhr, settings);
        });
        return deferred.promise();
    },

});

IssueReport = Backbone.Model.extend({

    // Default report information
    defaults: {
        meta: {
            id: null,
        },
        application: {
        },
        window: {
            location: window.location.href,
        },
    },

    uuid4: function() {
        // http://guid.us/GUID/JavaScript
        var S4 = function() { return (((1+Math.random())*0x10000)|0).toString(16).substring(1); }
        var uuid_str = (S4() + S4() + "-" + S4() + "-4" + S4().substr(0,3) + "-" + S4() + "-" + S4() + S4() + S4()).toLowerCase();
        return uuid_str;
    },

    initialize: function(options) {
        console.log('Initialize IssueReport');

        options = options || {};

        // Add basic information to report
        //   - Issue id
        //   - Application configuration object
        //   - Application runtime state
        //   - TODO: Request object
        this.get('meta').id              = this.uuid4();
        this.get('application').config   = opsChooserApp.config && opsChooserApp.config.toJSON() || {};
        this.get('application').metadata = opsChooserApp.metadata && opsChooserApp.metadata.toJSON() || {};

    },

});


IssueReporterGui = Backbone.Model.extend({

    initialize: function(options) {
        console.log('Initialize IssueReporterGui');
        this.reporter = new IssueReporter();
    },

    setup_ui: function() {
        var _this = this;
        $('.report-issue-problem').unbind('click');
        $('.report-issue-problem').click(function(event) {
            _this.problem({
                element: this,
                event: event,
            });
        });
    },

    problem: function(options) {

        options = options || {};

        options.what   = 'problem';
        options.remark = 'We experienced a problem with ...';

        // TODO: What about other targets like "log:error", "log:warning", "human:support", "human:user"?
        options.targets = 'email:support';

        this.dialog(options);
    },

    dialog: function(options) {

        options = options || {};

        var dialog = $('#issue-reporter-dialog');

        var what = $(options.element).data('dialog-what');
        options.what = what ? what : options.what;

        var remark = $(options.element).data('dialog-remark');
        options.remark = remark ? remark : options.remark;

        if (options.what) {
            dialog.find('#issue-reporter-what').val(options.what);
        } else {
            dialog.find('#issue-reporter-what').val('');
        }
        if (options.remark) {
            dialog.find('#issue-reporter-remark').val(htmlDecodeRelaxed(options.remark));
        } else {
            dialog.find('#issue-reporter-remark').val('');
        }

        // Setup and reset
        dialog.modal('show');

        // Prevent displaying the modal under backdrop
        // https://weblog.west-wind.com/posts/2016/Sep/14/Bootstrap-Modal-Dialog-showing-under-Modal-Background
        dialog.appendTo("body");

        dialog.find('#issue-reporter-send-button').show();
        dialog.find('#issue-reporter-status').empty();

        var setup_header = function() {
            var what = dialog.find('#issue-reporter-what').val();
            if (what == 'problem') {
                dialog.toggleClass('modal-warning', true);
                dialog.toggleClass('modal-success', false);
                dialog.find('#issue-reporter-label').html('<i class="icon-thumbs-down-alt"></i> Report problem');
            } else if (what == 'feature') {
                dialog.toggleClass('modal-warning', false);
                dialog.toggleClass('modal-success', true);
                dialog.find('#issue-reporter-label').html('<i class="icon-thumbs-up-alt"></i> Request feature');
            }
        };
        setup_header();

        dialog.find('#issue-reporter-what').unbind('change');
        dialog.find('#issue-reporter-what').on('change', function() {
            setup_header();
        });

        var _this = this;
        dialog.find('#issue-reporter-send-button').unbind('click');
        dialog.find('#issue-reporter-send-button').bind('click', function(event) {

            options.element_spinner = dialog.find('#issue-reporter-spinner');
            options.element_status  = dialog.find('#issue-reporter-status');

            options.dialog = {
                what: dialog.find('#issue-reporter-what').val(),
                remark: dialog.find('#issue-reporter-remark').val(),
            };
            _this.submit(options).then(function() {
                dialog.find('#issue-reporter-send-button').hide();
            });
        });

    },

    submit: function(options) {

        var element = options.element;

        var issue = new IssueReport({
            dialog: options.dialog,
            location: {
                origin: $(element).data('report-origin'),
                kind:   $(element).data('report-kind'),
                item:   $(element).data('report-item'),
            },
        });

        var html = $($(options.element).data('report-html')).html();
        if (html) {
            issue.set('html', html);
        }

        var spinner = $(options.element_spinner);
        var status_text = $(options.element_status);
        spinner.show();

        return this.reporter.send(issue, {targets: options.targets}).then(function() {
            spinner.hide();
            opsChooserApp.ui.user_alert(
                'Report sent successfully. Thank you for giving feedback, ' +
                'we will get back to you on this issue.', 'success', status_text);
        }).fail(function() {
            spinner.hide();
            opsChooserApp.ui.user_alert(
                'Automatic system report failed. Please get back to us via vendor contact address.', 'error', status_text);
        });
    },

});

var issueReporter = new IssueReporter();
//issueReporter.setup_stacktrace_interceptor({targets: 'log'});
issueReporter.setup_stacktrace_interceptor({targets: 'log,email:system'});
