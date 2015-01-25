// -*- coding: utf-8 -*-
// (c) 2014-2015 Andreas Motl, Elmyra UG

QueryBuilderView = Backbone.Marionette.ItemView.extend({

    template: "#querybuilder-template",

    initialize: function() {
        console.log('QueryBuilderView.initialize');
        //this.listenTo(this.model, "change", this.render);
        //this.listenTo(this, "item:rendered", this.setup_ui);
        this.config = this.templateHelpers.config = opsChooserApp.config;
        //this.setup_ui();
    },

    templateHelpers: {},

    onDomRefresh: function() {
        console.log('QueryBuilderView.onDomRefresh');
        this.setup_ui_base();
        this.setup_ui_actions();
    },

    setup_ui_base: function() {
        console.log('QueryBuilderView.setup_ui');

        var _this = this;


        // ------------------------------------------
        //   datasource selector
        // ------------------------------------------

        if (opsChooserApp.config.get('ftpro_enabled')) {
            $("#datasource > button[data-value='ftpro']").show();
        }

        // switch cql field chooser when selecting datasource
        // TODO: do it properly on the configuration data model
        $('#datasource').on('click', '.btn', function(event) {
            opsChooserApp.set_datasource($(this).data('value'));

            // hide query textarea for ftpro, if not in debug mode
            _this.setup_ui_query_textarea();
        });


        // ------------------------------------------
        //   user interface flavor chooser
        // ------------------------------------------

        $('#querybuilder-flavor-chooser button[data-toggle="tab"]').on('shown', function (e) {

            //e.target // activated tab
            //e.relatedTarget // previous tab

            var flavor = $(e.target).data('value');
            if (!flavor) return;

            // transfer values back to regular comfort form
            _this.comfort_form_zoomed_to_regular_data();

            // show/hide cql field chooser
            _this.cql_field_chooser_setup(flavor != 'cql');

            // application action: perform search
            // properly wire "send query" button
            $('.btn-query-perform').unbind('click');
            if (flavor == 'comfort') {

                _this.comfort_form_zoomed_to_regular_ui();

                // focus first field
                $('#patentnumber').focus();

                // hide action tools
                $('#querybuilder-comfort-actions').show();
                $('#querybuilder-cql-actions').hide();
                $('#querybuilder-numberlist-actions').hide();

                // hide history chooser
                $('#cql-history-chooser').show();

                // perform field-based search
                $('.btn-query-perform').click(function() {
                    $( "#querybuilder-comfort-form" ).submit();
                });

            } else if (flavor == 'cql') {

                // focus textarea
                $('#query').focus();

                // show action tools
                $('#querybuilder-comfort-actions').hide();
                $('#querybuilder-cql-actions').show();
                $('#querybuilder-numberlist-actions').hide();

                // show history chooser
                $('#cql-history-chooser').show();

                // convert query from form fields to cql expression
                _this.compute_comfort_query();

                // perform cql expression search
                $('.btn-query-perform').click(function() {
                    opsChooserApp.disable_reviewmode();
                    opsChooserApp.perform_search({reviewmode: false, clear: true, flavor: flavor});
                });

                // hide query textarea for ftpro, if not in debug mode
                _this.setup_ui_query_textarea();


            } else if (flavor == 'numberlist') {

                // focus textarea
                $('#numberlist').focus();

                // hide action tools
                $('#querybuilder-comfort-actions').hide();
                $('#querybuilder-cql-actions').hide();
                $('#querybuilder-numberlist-actions').show();

                // hide history chooser
                $('#cql-history-chooser').hide();

                // switch datasource to epo
                opsChooserApp.set_datasource('ops');

                // perform numberlist search
                $('.btn-query-perform').click(function() {
                    opsChooserApp.disable_reviewmode();
                    opsChooserApp.perform_numberlistsearch({reviewmode: false, clear: true});
                });

            }
        });


        // ------------------------------------------
        //   submit search
        // ------------------------------------------

        $( "#querybuilder-comfort-form" ).unbind();
        $( "#querybuilder-comfort-form" ).submit(function( event ) {

            // transfer values from zoomed fields
            _this.comfort_form_zoomed_to_regular_data();

            var query_data = _this.get_comfort_form_data();

            // convert query from form fields to cql expression
            _this.compute_comfort_query().then(function() {

                //$("#querybuilder-flavor-chooser button[data-flavor='cql']").tab('show');
                opsChooserApp.disable_reviewmode();
                opsChooserApp.perform_search({reviewmode: false, clear: true, flavor: _this.get_flavor(), query_data: query_data});

            });

        });

        // define default search action when using "Start search" button
        $('.btn-query-perform').unbind('click');
        $('.btn-query-perform').click(function() {
            $( "#querybuilder-comfort-form" ).submit();
        });


        // ------------------------------------------
        //   full-cycle mode chooser
        // ------------------------------------------

        // https://github.com/twbs/bootstrap/issues/2380#issuecomment-13981357
        $('.btn-full-cycle').on('click', function(e) {
            e.stopPropagation();
            if( $(this).attr('data-toggle') != 'button' ) { // don't toggle if data-toggle="button"
                $(this).toggleClass('active');
            }
            opsChooserApp.config.set('mode.full-cycle', $(this).hasClass( 'active' ));

        });

        // --------------------------------------------
        //   intercept and reformat clipboard content
        // --------------------------------------------
        /*
        $("#query").on("paste", function(e) {

            // only run interceptor if content of target element is empty
            if ($(this).val()) return;

            e.preventDefault();

            var text = (e.originalEvent || e).clipboardData.getData('text');

        });
        */

    },

    // hide query textarea for ftpro, if not in debug mode
    setup_ui_query_textarea: function() {

        if (opsChooserApp.config.get('debug')) {
            return;
        }

        if (opsChooserApp.get_datasource() == 'ftpro') {
            $('#query').hide();
            $('#query').parent().find('#query-alert').remove();
            $('#query').parent().append('<div id="query-alert" class="alert alert-default"><br/><br/>Expert mode not available with data source "FulltextPRO".</div>');
            var alert_element = $('#query').parent().find('#query-alert');
            alert_element.height($('#query').height() - 18);
            //alert_element.marginBottom($('#query').marginBottom());
        } else {
            $('#query').parent().find('#query-alert').remove();
            $('#query').show();
        }

    },

    query_empty: function() {
        return _.isEmpty($('#query').val().trim());
    },
    check_query_empty: function(options) {
        if (this.query_empty()) {
            opsChooserApp.ui.notify('Query expression is empty', {type: 'warning', icon: options.icon});
            return true;
        }
        return false;
    },

    numberlist_empty: function() {
        return _.isEmpty($('#numberlist').val().trim());
    },
    check_numberlist_empty: function(options) {
        if (this.numberlist_empty()) {
            opsChooserApp.ui.notify('Numberlist is empty', {type: 'warning', icon: options.icon});
            return true;
        }
        return false;
    },

    get_comfort_form_entries: function(options) {
        options = options || {};
        var entries = [];
        _.each($('#querybuilder-comfort-form').find('input'), function(field) {
            var f = $(field);
            var name = f.attr('name');
            var value = f.val();
            if (!value && options.skip_empty) {
                return;
            }
            var label = name + ':';
            label = _.string.rpad(label, 16, ' ');
            entries.push(label + value);
        });
        return entries;
    },

    setup_ui_actions: function() {

        var _this = this;

        // ------------------------------------------
        //   cql query area action tools
        // ------------------------------------------

        // display all comfort form values
        $('#btn-comfort-display-values').unbind('click');
        $('#btn-comfort-display-values').click(function() {

            var copy_button = '<a id="comfort-form-copy-button" role="button" class="btn"><i class="icon-copy"></i> &nbsp; Copy to clipboard</a>';

            var entries = _this.get_comfort_form_entries();
            var data = entries.join('\n');
            var modal_html = '<pre>' + data + '</pre>' + copy_button;

            var box = bootbox.dialog(
                modal_html, [{
                    "label": 'OK',
                    "icon" : 'OK',
                    "callback": null,
                }],
                {header: 'Contents of comfort form'});
            //log('box:', box);

            // bind clipboard copy button
            var copy_button = box.find('#comfort-form-copy-button');
            _ui.copy_to_clipboard_bind_button('text/plain', data, {element: copy_button[0], wrapper: box[0]});

        });

        // clear all comfort form values
        $('#btn-comfort-clear').unbind('click');
        $('#btn-comfort-clear').click(function() {
            _this.clear_comfort_form();
        });

        // clear the whole expression (export form)
        $('#btn-query-clear').unbind('click');
        $('#btn-query-clear').click(function() {
            $('#query').val('').focus();
        });

        // transform query: open modal dialog to choose transformation kind
        $('#btn-query-transform').unbind('click');
        $('#btn-query-transform').click(function() {
            if (_this.check_query_empty({'icon': 'icon-exchange'})) { return; }
            $('#clipboard-modifier-chooser').modal('show');
        });

        // open query chooser
        $('#btn-query-history').unbind('click');
        $('#btn-query-history').click(function(e) {

            // setup select2 widget
            _this.cql_history_chooser_setup();

            var opened = $('#cql-history-chooser').hasClass('open');
            var chooser_widget = $('#cql-history-chooser-select2');

            // if already opened, skip event propagation and just reopen the widget again
            if (opened) {
                e.preventDefault();
                e.stopPropagation();
                chooser_widget.select2('open');

                // open select2 widget *after* dropdown has been opened
            } else {
                // TODO: use "shown.bs.dropdown" event when migrating to bootstrap3
                setTimeout(function() {
                    chooser_widget.select2('open');
                });
            }
        });

        // share via url, with ttl
        $('#btn-query-permalink').unbind('click');
        $('#btn-query-permalink').click(function(e) {

            e.preventDefault();
            if (_this.check_query_empty({'icon': 'icon-external-link'})) { return; }

            var anchor = this;

            var query_state = {
                mode: 'liveview',
                context: 'viewer',
                project: 'query-permalink',
                query: opsChooserApp.get_query(),
                datasource: opsChooserApp.get_datasource(),
            };

            opsChooserApp.permalink.make_uri_opaque(query_state).then(function(url) {

                // v1: open url
                //$(anchor).attr('href', url);

                // v2: open permalink popover
                e.stopPropagation();
                opsChooserApp.permalink.popover_show(anchor, url, {
                    title: 'External query review',
                    intro:
                        '<small>' +
                            'This offers a link for external/anonymous users to review the current query. ' +
                        '</small>',
                    ttl: true,
                });

            });
        });


        // transform query: modifier kind selected in dialog
        $('.btn-clipboard-modifier').click(function() {

            // get field name and operator from dialog
            var modifier = $(this).data('modifier');
            var operator = $('#clipboard-modifier-operator').find('.btn.active').data('value') || 'OR';

            // close dialog
            $('#clipboard-modifier-chooser').modal('hide');

            // compute new query content
            var text = $('#query').val().trim();
            if (_.str.contains(text, '=')) {
                return;
            }
            var entries = text.split('\n');
            var query = _(entries).map(function(item) {
                return modifier + '=' + '"' + item + '"';
            }).join(' ' + operator + ' ');

            // set query content and focus element
            $('#query').val(query);
            $('#query').focus();

        });


        // normalize numberlist
        $('#btn-numberlist-normalize').unbind('click');
        $('#btn-numberlist-normalize').click(function(e) {
            e.preventDefault();
            if (_this.check_numberlist_empty({'icon': 'icon-exchange'})) { return; }

            _this.normalize_numberlist($('#numberlist').val()).then(function(response) {
                var numbers_valid = response['numbers-normalized'] && response['numbers-normalized']['valid'];
                var numbers_invalid = response['numbers-normalized'] && response['numbers-normalized']['invalid'];

                // replace numberlist in ui by normalized one
                $('#numberlist').val(numbers_valid.join('\n'));

                // display invalid patent numbers
                if (_.isEmpty(numbers_invalid)) {
                    opsChooserApp.ui.notify(
                        'Patent numbers normalized successfully',
                        {type: 'success', icon: 'icon-exchange', right: true});
                } else {
                    var message = 'Number normalization failed for:<br/><br/><pre>' + numbers_invalid.join('\n') + '</pre>';
                    opsChooserApp.ui.user_alert(message, 'warning');

                }
            });
        });

    },

    clear_comfort_form: function() {
        $('#querybuilder-comfort-form').find('input').val('');
    },

    normalize_numberlist: function(payload) {
        var deferred = $.Deferred();
        $.ajax({
            method: 'post',
            url: '/api/util/numberlist?normalize=true',
            beforeSend: function(xhr, settings) {
                xhr.requestUrl = settings.url;
            },
            async: false,
            sync: true,
            data: payload,
            contentType: "text/plain; charset=utf-8",
        }).success(function(response, status, options) {
            if (response) {
                deferred.resolve(response);
            } else {
                opsChooserApp.ui.notify('Number normalization failed (empty response)', {type: 'warning', icon: 'icon-exchange', right: true});
                deferred.reject();
            }
        }).error(function(xhr, settings) {
            opsChooserApp.ui.propagate_alerts(xhr);
            deferred.reject();
        });
        return deferred.promise();
    },

    setup_quick_cql_builder: function() {

        // ------------------------------------------
        //   cql quick query builder
        //   NOTE: currently defunct
        // ------------------------------------------
        $('.btn-cql-boolean').button();
        $('#cql-quick-operator').find('.btn-cql-boolean').click(function() {
            $('#query').focus();
        });
        $('.btn-cql-field').click(function() {

            var query = $('#query').val();
            var operator = $('#cql-quick-operator').find('.btn-cql-boolean.active').data('value');
            var attribute = $(this).data('value');

            var position = $('#query').caret();
            var do_op = false;
            var do_att = true;
            //console.log('position: ' + position);

            var leftchar;
            if (position != 0) {
                do_op = true;

                // insert nothing if we're right off an equals "="
                leftchar = query.substring(position - 1, position);
                //console.log('leftchar: ' + leftchar);
                if (leftchar == '=') {
                    do_op = false;
                    do_att = false;
                }

                // don't insert operation if there's already one left of the cursor
                var fiveleftchar = query.substring(position - 5, position).toLowerCase();
                //console.log('fiveleftchar: ' + fiveleftchar);
                if (_.string.contains(fiveleftchar, 'and') || _.string.contains(fiveleftchar, 'or')) {
                    do_op = false;
                }

            }

            // manipulate query by inserting relevant
            // parts at the current cursor position
            var leftspace = (!leftchar || leftchar == ' ') ? '' : ' ';

            if (do_op)
                $('#query').caret(leftspace + operator);
            if (do_att)
                $('#query').caret((do_op ? ' ' : leftspace) + attribute);

            $('#query').focus();
        });

    },

    cql_field_chooser_get_data: function(datasource) {
        if (datasource == 'ops') {
            return OPS_CQL_FIELDS;

        } else if (datasource == 'depatisnet') {
            return DEPATISNET_CQL_FIELDS;

        } else {
            return [];

        }
    },
    cql_field_chooser_setup: function(hide) {

        // TODO: reduce conditional weirdness

        var datasource = opsChooserApp.get_datasource();
        var queryflavor = opsChooserApp.queryBuilderView.get_flavor();
        if (hide || !datasource || _(['review', 'google', 'ftpro']).contains(datasource) || queryflavor != 'cql') {
            var container = $('#cql-field-chooser')[0].previousSibling;
            $(container).hide();
            return;
        }
        var data = this.cql_field_chooser_get_data(datasource);
        $('#cql-field-chooser').select2({
            placeholder: 'CQL field symbols' + ' (' + datasource + ')',
            data: { results: data },
            dropdownCssClass: "bigdrop",
            escapeMarkup: function(text) { return text; },
        });
        $('#cql-field-chooser').on('change', function(event) {

            var value = $(this).val();
            if (!value) return;

            //console.log(value);

            var query = $('#query').val();
            var position = $('#query').caret();
            var leftchar = query.substring(position - 1, position);

            // skip insert if we're right behind a "="
            if (leftchar == '=') return;

            // insert space before new field if there is none and we're not at the beginning
            if (leftchar != ' ' && position != 0) value = ' ' + value;

            $('#query').caret(value + '=');
            $(this).data('select2').clear();

        });

    },

    cql_history_chooser_get_data: function() {

        log('cql_history_chooser_get_data');

        var deferred = $.Deferred();

        // fetch query objects and sort descending by creation date
        var _this = this;
        $.when(opsChooserApp.project.fetch_queries()).then(function() {
            var query_collection = opsChooserApp.project.get('queries');
            query_collection = sortCollectionByField(query_collection, 'created', 'desc');
            var deferreds = [];
            var chooser_data = query_collection.map(function(query) {
                return _this.query_model_repr(query);
            });
            deferred.resolve(chooser_data);

        }).fail(function() {
            deferred.reject();
        });

        return deferred.promise();


        var queries = opsChooserApp.project.get('queries');
        var chooser_data = _(queries).unique().map(function(query) {
            return { id: query, text: query };
        });
        return chooser_data;
    },

    query_model_repr: function(query) {

        var flavor = query.get('flavor');
        var datasource = query.get('datasource');
        var query_data = query.get('query_data');
        var created = query.get('created');
        var result_count = query.get('result_count');

        // compute title
        var title = query.get('query_expression');
        if ((flavor == 'comfort' || datasource == 'ftpro') && query_data && _.isObject(query_data['criteria'])) {
            // serialize query_data criteria
            var entries = _.map(query_data['criteria'], function(value, key) {
                // add serialized representation of fulltext modifiers if not all(modifiers) == true
                if (key == 'fulltext' && query_data['modifiers'] && query_data['modifiers']['fulltext']) {
                    if (_.every(_.values(query_data['modifiers']['fulltext']))) {
                        value += ' [all]';

                    } else {
                        var modifiers = _.objFilter(query_data['modifiers']['fulltext'], function(value, key) {
                            return Boolean(value);
                        });
                        value += ' [' + _.keys(modifiers).join(',') + ']';

                    }
                }
                return key + ': ' + value;
            });
            title = entries.join(', ');
        }
        created = moment(created).fromNow();

        var datasource_title = datasource;
        if (datasource == 'ops') {
            datasource_title = 'EPO';
        } else if (datasource == 'depatisnet') {
            datasource_title = 'DPMA';
        } else if (datasource == 'ftpro') {
            datasource_title = 'FtPRO';
        }

        title += '<div class="pull-right"><small>' + [
            flavor,
            datasource_title,
            created,
            (result_count ? result_count : 'no') + ' hits'
        ].join(', ') + '</small></div><div class="clearfix"></div>';

        var entry = {
            id: query,
            text: title,
        };
        return entry;

    },

    cql_history_chooser_setup: function() {
        var projectname = opsChooserApp.project.get('name');

        var chooser_widget = $('#cql-history-chooser-select2');

        // initialize empty cql history chooser widget
        chooser_widget.select2({
            placeholder: 'Query history' + ' (' + projectname + ')',
            data: { results: [] },
            dropdownCssClass: "bigdrop",
            escapeMarkup: function(text) { return text; },
        });

        // when query was selected, put it into cql query input field
        var _this = this;
        chooser_widget.unbind('change');
        chooser_widget.on('change', function(event) {

            $(this).unbind('change');

            // this gets the "id" attribute of an entry in select2 `data`
            var query_object = $(this).val();

            // transfer history data to current querybuilder state
            if (query_object) {

                var flavor = query_object.get('flavor');
                if (flavor == 'cql') {
                    _this.disable_compute_comfort_query = true;
                }
                _this.set_flavor(flavor);

                opsChooserApp.set_datasource(query_object.get('datasource'));

                if (flavor == 'comfort') {
                    var data = query_object.get('query_data');
                    _this.clear_comfort_form();
                    _this.set_comfort_form_data(data);

                } else if (flavor == 'cql') {
                    var expression = query_object.get('query_expression');
                    _this.clear_comfort_form();
                    $('#query').val(expression);
                }

            }

            // destroy widget and close dropdown container
            $(this).data('select2').destroy();
            $(this).dropdown().toggle();

        });

        // load query history data and propagate to history chooser
        this.cql_history_chooser_get_data().then(function(data) {
            chooser_widget.select2({
                data: data,
                escapeMarkup: function(text) { return text; },
            });
        });

    },

    setup_comfort_form: function() {
        var form = $('#querybuilder-comfort-form');
        var datasource = opsChooserApp.get_datasource();

        var _this = this;

        // fix submit by enter for internet explorer
        form.handle_enter_keypress();

        // hide publication date for certain search backends
        var pubdate = form.find("input[name='pubdate']").closest("div[class='control-group']");
        if (_(['ops', 'depatisnet', 'ftpro']).contains(datasource)) {
            pubdate.show();
        } else if (_(['google']).contains(datasource)) {
            pubdate.hide();
        }

        // hide citations for certain search backends
        var citation = form.find("input[name='citation']").closest("div[class='control-group']");
        if (_(['ops', 'depatisnet']).contains(datasource)) {
            citation.show();
        } else if (_(['google', 'ftpro']).contains(datasource)) {
            citation.hide();
        }

        // amend placeholder values for certain search backends
        var patentnumber = form.find("input[name='patentnumber']");
        if (_(['google', 'ftpro']).contains(datasource)) {
            patentnumber.attr('placeholder', patentnumber.data('placeholder-single'));
        } else {
            patentnumber.attr('placeholder', patentnumber.data('placeholder-multi'));
        }

        // enrich form fields with actions
        _.each(form.find(".input-prepend"), function(item) {

            // populate field value with placeholder value on demand
            $(item).find('.add-on.add-on-label').on('click', function(ev) {
                var input_element = $(item).find('input');
                if (!input_element.val()) {
                    var demo_value = input_element.attr('placeholder');
                    if (input_element.data('demo')) {
                        demo_value = input_element.data('demo');
                    }
                    input_element.val(demo_value);
                }
            });

            // zoom input field to textarea
            $(item).find('.add-on.add-on-zoom').on('click', function(ev) {
                var input_element = $(item).find('input');
                _this.comfort_form_regular_to_zoomed(input_element);
            });
        });

        // conditionally display fulltext-modifier-chooser
        if (_(['ftpro']).contains(datasource)) {
            $('#fulltext-modifier-chooser').show();
            $('#fulltext-textarea-container').removeClass('span12').addClass('span11');
            $('#fulltext-textarea-container').find('textarea').removeClass('span11').addClass('span10');
        } else {
            $('#fulltext-modifier-chooser').hide();
            $('#fulltext-textarea-container').removeClass('span11').addClass('span12');
            $('#fulltext-textarea-container').find('textarea').removeClass('span10').addClass('span11');
        }

    },

    comfort_form_regular_to_zoomed: function(input_element) {

        var _this = this;

        var fieldname = input_element.attr('name');
        var value = input_element.val();
        var fieldset = $('#querybuilder-comfort-form > fieldset');
        fieldset.children('.field-regular').hide();

        var zoomed_element = fieldset.children('#' + fieldname + '-zoomed');
        zoomed_element.fadeIn();

        var textarea = zoomed_element.find('textarea');
        textarea.val(value);
        textarea.focus();

        opsChooserApp.hotkeys.querybuilder_zoomed_hotkeys(textarea, input_element);
        opsChooserApp.hotkeys.querybuilder_hotkeys(textarea);

    },

    comfort_form_zoomed_to_regular_data: function() {
        var fieldset = $('#querybuilder-comfort-form > fieldset');
        var zoomed = fieldset.children('.field-zoomed').is(":visible");
        if (zoomed) {
            var textarea = fieldset.children('.field-zoomed:visible').find('textarea');
            var fieldname = textarea.data('name');
            var value = textarea.val();
            fieldset.find('input[name="' + fieldname + '"]').val(value);
        }
    },

    comfort_form_zoomed_to_regular_ui: function(input_element) {
        var fieldset = $('#querybuilder-comfort-form > fieldset');
        fieldset.children('.field-zoomed').hide();
        fieldset.children('.field-regular').fadeIn();
        input_element && input_element.focus();
    },

    set_comfort_form_data: function(data, options) {
        options = options || {};

        // populate input fields
        var form = $('#querybuilder-comfort-form');
        _.each(data['criteria'], function(value, key) {
            var element = form.find('input[name="' + key + '"]');
            element.val(value);
        });

        // populate fulltext modifiers
        if (data['modifiers'] && _.isObject(data['modifiers']['fulltext'])) {
            _.each(data['modifiers']['fulltext'], function(value, key) {
                var element = $(form).find($('button[data-name="fulltext"][data-modifier="' + key + '"]'));
                if (value) {
                    element.addClass('active');
                } else {
                    element.removeClass('active');
                }
            });
        }

    },

    get_comfort_form_data: function() {

        var form = $('#querybuilder-comfort-form');

        var datasource = opsChooserApp.get_datasource();

        var criteria = {};
        var modifiers = {};

        // collect input fields
        var fields = $(form).find($('input'));
        _.each(fields, function(item) {
            if (item.value) {
                criteria[item.name] = item.value;
            }
        });

        // skip if collected criteria is empty
        if (_.isEmpty(criteria)) {
            return;
        }

        // collect fulltext modifiers
        var buttons = $(form).find($('button[data-name="fulltext"]'));
        var modifiers = {};
        _.each(buttons, function(button) {
            var name = $(button).data('name');
            var modifier = $(button).data('modifier');
            var state = $(button).hasClass('active');

            var defaults = {};
            defaults[name] = {};
            _.defaults(modifiers, defaults);

            modifiers[name][modifier] = state;
        });

        var payload = {
            format: 'comfort',
            datasource: datasource,
            criteria: criteria,
            modifiers: modifiers,
            //query: opsChooserApp.config.get('query'),
        };
        return payload;

    },

    compute_comfort_query: function() {

        if (this.disable_compute_comfort_query) {
            this.disable_compute_comfort_query = false;
            var deferred = $.Deferred();
            deferred.reject();
            return deferred;
        }

        var payload = this.get_comfort_form_data();
        if (_.isEmpty(payload)) {
            var deferred = $.Deferred();
            deferred.reject();
            return deferred;
        }

        log('comfort form query:', JSON.stringify(payload));

        //$("#query").val('');
        $("#keywords").val('[]');
        return this.compute_query_expression(payload).then(function(expression, keywords) {
            $("#query").val(expression);
            $("#keywords").val(keywords);

        }).fail(function() {
            $("#query").val('');
            $("#keywords").val('');
            opsChooserApp.ui.reset_content({documents: true, keep_notifications: true});
        });
    },

    compute_query_expression: function(payload) {
        var deferred = $.Deferred();
        $.ajax({
            method: 'post',
            url: '/api/util/query-expression',
            beforeSend: function(xhr, settings) {
                xhr.requestUrl = settings.url;
            },
            async: false,
            sync: true,
            data: JSON.stringify(payload),
            contentType: "application/json; charset=utf-8",
        }).success(function(payload, status, options) {
            if (payload) {
                var keywords = options.getResponseHeader('X-Elmyra-Query-Keywords');
                deferred.resolve(payload, keywords);
            } else {
                deferred.resolve('', '[]');
            }
        }).error(function(xhr, settings) {
            opsChooserApp.ui.propagate_alerts(xhr);
            deferred.reject();
        });
        return deferred.promise();
    },

    get_flavor: function() {
        var flavor = $('#querybuilder-flavor-chooser > .btn.active').data('value');
        return flavor;
    },

    set_flavor: function(flavor) {
        $("#querybuilder-flavor-chooser .btn[data-value='" + flavor + "']").tab('show');
    },

    set_numberlist: function(numberlist) {
        if (!_.isEmpty(numberlist)) {
            this.set_flavor('numberlist');

            // .html() does not work in IE
            //$('#numberlist').html(numberlist);
            $('#numberlist').val(numberlist);

            opsChooserApp.perform_numberlistsearch();
        }
    },

});


// setup component
opsChooserApp.addInitializer(function(options) {

    this.queryBuilderView = new QueryBuilderView({});
    this.queryBuilderRegion.show(this.queryBuilderView);

    // Special bootstrap handling for numberlist=EP666666,EP666667:
    this.listenTo(this, 'application:ready', function() {
        var numberlist_raw = this.config.get('numberlist');
        if (numberlist_raw) {
            var numberlist = decodeURIComponent(numberlist_raw);
            this.queryBuilderView.set_numberlist(numberlist);
        }
    });

});
