// -*- coding: utf-8 -*-
// (c) 2013-2018 Andreas Motl <andreas.motl@ip-tools.org>
require('select2/select2.js');
require('select2/select2.css');
require('jquery-caret-plugin/dist/jquery.caret.js');
var bootbox = require('bootbox');

require('patzilla.lib.radioplus');
var FIELDS_KNOWLEDGE = require('./expression-fields.js').FIELDS_KNOWLEDGE;

QueryBuilderView = Backbone.Marionette.ItemView.extend({

    template: require('./querybuilder.html'),

    initialize: function() {
        console.log('QueryBuilderView.initialize');
        //this.listenTo(this.model, "change", this.render);
        //this.listenTo(this, "item:rendered", this.setup_ui);
        this.config = this.templateHelpers.config = navigatorApp.config;
        //this.setup_ui();
        this.radios = new RadioPlus();
    },

    templateHelpers: {},

    onDomRefresh: function() {
        console.log('QueryBuilderView.onDomRefresh');
        this.setup_ui_base();
        this.setup_ui_actions();
    },

    get_datasource_info: function() {
        var datasource = navigatorApp.get_datasource();
        datasource_info = navigatorApp.datasource_info(datasource);
        if (!datasource_info) {
            datasource_info = {
                'querybuilder': {},
            }
        }
        //log('get_datasource_info:', datasource, datasource_info);
        return datasource_info;
    },

    // Set dirty when modifying any search parameter
    wire_dirty_events: function() {

        // Capture editing comfort search field
        $('#querybuilder-comfort-form input').off('input').on('input', function() {
            navigatorApp.metadata.dirty(true);
        });

        // Capture editing expert query expression
        $('#query').off('input').on('input', function() {
            navigatorApp.metadata.dirty(true);
        });

        // Capture choosing a datasource
        $('#datasource button').off('click').on('click', function() {
            navigatorApp.metadata.dirty(true);
        });

        // Capture toggling any modifier button
        this.radios.off('toggle').on('toggle', function() {
            navigatorApp.metadata.dirty(true);
        });

    },

    setup_ui_base: function() {
        console.log('QueryBuilderView.setup_ui');

        var _this = this;

        // -------------------
        // Datasource selector
        // -------------------
        this.display_datasource_buttons();

        // Switch cql field chooser when selecting datasource
        // TODO: do it properly on the configuration data model
        $('#datasource').on('click', '.btn', function(event) {

            // Set datasource in model
            var datasource = $(this).data('value');

            var datasource_info = navigatorApp.datasource_info(datasource);
            //log('datasource_info:', datasource_info);

            if (datasource_info === undefined) {
                navigatorApp.ui.work_in_progress();
            }

            // Set datasource in model
            navigatorApp.set_datasource(datasource);

            // Hide query textarea for some data sources, if not in debug mode
            _this.setup_ui_query_textarea();
        });


        // Flag search metadata as dirty when modifying any search field
        this.wire_dirty_events();


        // -----------------------------
        // User interface flavor chooser
        // -----------------------------

        $('#querybuilder-flavor-chooser button[data-toggle="tab"]').on('shown', function (e) {

            //e.target // activated tab
            //e.relatedTarget // previous tab

            var flavor = $(e.target).data('value');
            if (!flavor) return;

            // transfer values back to regular comfort form
            _this.comfort_form_zoomed_to_regular_data();

            // show/hide cql field chooser
            _this.setup_cql_field_chooser(flavor != 'cql');

            // show all search backends
            _this.display_datasource_buttons();

            // application action: perform search
            // properly wire "send query" button
            $('.btn-query-perform').off('click');
            if (flavor == 'comfort') {

                // Setup zoomed fields
                _this.comfort_form_zoomed_to_regular_ui();

                // Focus first field
                $('#patentnumber').trigger('focus');

                // Hide action tools
                $('#querybuilder-comfort-actions').show();
                $('#querybuilder-cql-actions').hide();
                $('#querybuilder-numberlist-actions').hide();

                // Hide history chooser
                $('#cql-history-chooser').show();

                // Perform field-based search
                $('.btn-query-perform').on('click', function() {
                    $( "#querybuilder-comfort-form" ).trigger('submit');
                });

            // TODO: Rename "cql" to "expert"
            } else if (flavor == 'cql') {

                // Focus textarea
                $('#query').trigger('focus');

                // Show action tools
                $('#querybuilder-comfort-actions').hide();
                $('#querybuilder-cql-actions').show();
                $('#querybuilder-numberlist-actions').hide();

                // Show history chooser
                $('#cql-history-chooser').show();

                // Optionally show filter field
                var datasource_info = _this.get_datasource_info();
                if (datasource_info.querybuilder.enable_separate_filter_expression) {
                    $('#cql-filter-container').show();
                } else {
                    $('#cql-filter-container').hide();
                }

                // Convert query from form fields to cql expression
                _this.compute_comfort_query();

                // Perform CQL expression search
                $('.btn-query-perform').on('click', function() {
                    navigatorApp.start_expert_search();
                });

                // Hide query textarea for some data sources, if not in debug mode
                _this.setup_ui_query_textarea();


            } else if (flavor == 'numberlist') {

                // focus textarea
                $('#numberlist').trigger('focus');

                // hide action tools
                $('#querybuilder-comfort-actions').hide();
                $('#querybuilder-cql-actions').hide();
                $('#querybuilder-numberlist-actions').show();

                // hide history chooser
                $('#cql-history-chooser').hide();

                // switch datasource to epo
                navigatorApp.set_datasource('ops');

                // hide other search backends, only display OPS
                _this.display_datasource_buttons(['ops']);

                // perform numberlist search
                $('.btn-query-perform').on('click', function() {
                    navigatorApp.disable_reviewmode();
                    navigatorApp.populate_metadata();
                    navigatorApp.perform_numberlistsearch({reviewmode: false, reset: ['pagination_current_page', 'page_size']});
                });

            }
        });


        // ------------------------------------------
        //   common form behavior
        // ------------------------------------------

        //   mode: full-cycle, display all document kinds
        //   mode: remove patent family members

        // workaround for making "hasClass('active')" work stable
        // https://github.com/twbs/bootstrap/issues/2380#issuecomment-13981357
        var common_buttons = $('.btn-syntax, .btn-full-cycle, .btn-family-swap-ger, .btn-mode-order, .btn-family-remove, .btn-family-replace, .btn-family-full');
        common_buttons.off('click');
        common_buttons.on('click', function(e) {

            var already_active = $(this).hasClass('active');
            _this.radios.button_behaviour(this, e);

            // set label text
            _this.radios.label_behaviour(this, already_active);

            // When clicking a mode button which augments search behavior, recompute upstream query expression
            // for search backends where query_data modifiers already influence the expression building.
            var datasource_info = _this.get_datasource_info();
            if (datasource_info.recompute_query_on_modechange) {
                _this.compute_comfort_query();
            }
        });


        // ------------------------------------------
        //   comfort form search
        // ------------------------------------------

        $( "#querybuilder-comfort-form" ).off();
        $( "#querybuilder-comfort-form" ).on('submit', function( event ) {

            // Transfer values from zoomed modifier fields
            _this.comfort_form_zoomed_to_regular_data();

            // Compute CQL expression from form fields
            _this.compute_comfort_query().then(function() {

                // Get information from form fields
                var query_data = _this.get_comfort_form_data();

                //$("#querybuilder-flavor-chooser button[data-flavor='cql']").tab('show');
                navigatorApp.start_search({flavor: 'comfort', query_data: query_data});
            });

        });

        // define default search action when using "Start search" button
        $('.btn-query-perform').off('click');
        $('.btn-query-perform').on('click', function() {
            $( "#querybuilder-comfort-form" ).trigger('submit');
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

    display_datasource_buttons: function(whitelist) {

        // Hide all buttons as we will incrementally enable them.
        $('#datasource button').hide();

        // Acquire vendor settings.
        var vendor = navigatorApp.config.get('vendor');

        // Compute data sources the user is allowed to see.
        if (_.isEmpty(whitelist)) {
            whitelist = navigatorApp.config.get('datasources_enabled');
        }

        // Display buttons for switching to different data sources.
        var _this = this;
        _.each(whitelist, function(item) {
            var element = _this.get_datasource_button(item);
            element.show();
        });

    },

    get_datasource_button: function(datasource) {
        var vendor = navigatorApp.config.get('vendor');
        var element = $("#datasource > button[data-value='" + datasource + "'][data-vendor='" + vendor + "']");
        if (!$(element).exists()) {
            element = $("#datasource > button[data-value='" + datasource + "']:not([data-vendor])");
        }
        return element;
    },

    // Hide query textarea for some data sources, if not in debug mode
    setup_ui_query_textarea: function() {

        if (navigatorApp.config.get('debug')) {
            return;
        }

        if (this.get_datasource_info().querybuilder.disable_raw_query) {
            $('#query').hide();
            $('#query').parent().find('#query-alert').remove();
            $('#query').parent().append(
                '<div id="query-alert" class="alert alert-default">' +
                'Expert mode not available for this data source.' +
                '</div>');
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
        options = options || {};
        if (this.query_empty()) {
            navigatorApp.ui.notify('Query expression is empty', {type: 'warning', icon: options.icon});
            return true;
        }
        return false;
    },

    numberlist_empty: function() {
        return _.isEmpty($('#numberlist').val().trim());
    },
    check_numberlist_empty: function(options) {
        if (this.numberlist_empty()) {
            navigatorApp.ui.notify('Numberlist is empty', {type: 'warning', icon: options.icon});
            return true;
        }
        return false;
    },

    data_is_dirty: function() {
        return navigatorApp.metadata.dirty();
    },
    check_data_is_dirty: function(options) {
        options = options || {};
        if (this.data_is_dirty()) {
            navigatorApp.ui.notify(
                'Search parameters empty, modified or invalid. \n' +
                'Please submit valid search first.',
                {type: 'warning', icon: options.icon});
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
        $('#btn-comfort-display-values').off('click');
        $('#btn-comfort-display-values').on('click', function() {

            var copy_button = '<a id="comfort-form-copy-button" role="button" class="btn"><i class="icon-copy"></i> &nbsp; Copy to clipboard</a>';

            var entries = _this.get_comfort_form_entries();
            var data = entries.join('\n') + '\n';
            var modal_html = '<pre>' + data + '</pre>' + copy_button;

            var box = bootbox.alert({
                title: 'Contents of comfort form',
                message: modal_html,
            });

            // bind clipboard copy button
            var copy_button = box.find('#comfort-form-copy-button');
            navigatorApp.ui.copy_to_clipboard_bind_button('text/plain', data, {element: copy_button[0], wrapper: box[0]});

        });

        // clear all comfort form values
        $('#btn-comfort-clear').off('click');
        $('#btn-comfort-clear').on('click', function() {
            _this.clear_comfort_form();
        });

        // clear the whole expression (expert form)
        $('#btn-query-clear').off('click');
        $('#btn-query-clear').on('click', function() {
            $('#query').val('').trigger('focus');
            $('#cql-filter').val('');
        });

        // transform query: open modal dialog to choose transformation kind
        $('#btn-query-transform').off('click');
        $('#btn-query-transform').on('click', function() {
            if (_this.check_query_empty({'icon': 'icon-exchange'})) { return; }

            var dialog = $('#query-transform-dialog');
            dialog.modal('show');

            // Prevent displaying the modal under backdrop
            // https://weblog.west-wind.com/posts/2016/Sep/14/Bootstrap-Modal-Dialog-showing-under-Modal-Background
            dialog.appendTo("body");
        });

        // Open query chooser
        $('#btn-query-history').off('click');
        $('#btn-query-history').on('click', function(e) {

            // Setup select2 widget
            _this.cql_history_chooser_setup().then(function() {

                var opened = $('#cql-history-chooser').hasClass('open');

                // If already opened, skip event propagation to prevent wrong parent nesting
                if (opened) {
                    e.preventDefault();
                    e.stopPropagation();
                }

                // Open select2 widget *after* dropdown has been opened
                // TODO: use "shown.bs.dropdown" event when migrating to bootstrap3
                var chooser_widget = $('#cql-history-chooser-select2');
                setTimeout(function() {
                    chooser_widget.select2('open');
                });

            });

        });

        // Share query via opaque link, with expiration time (ttl)
        $('#btn-query-permalink').off('click');
        $('#btn-query-permalink').on('click', function(e) {

            e.preventDefault();
            e.stopPropagation();

            // Sanity check: Don't share empty queries
            if (_this.check_query_empty({'icon': 'icon-external-link'})) { return; }

            // Sanity check: Don't share dirty queries
            if (_this.check_data_is_dirty({'icon': 'icon-external-link'})) { return; }

            // Create viewstate context for liveview mode
            var viewstate = navigatorApp.permalink.query_parameters_viewstate();
            _.extend(viewstate, {
                mode: 'liveview',
                context: 'viewer',
                project: 'query-permalink',
            });
            //log('viewstate:', viewstate);

            // Create opaque link for propagating viewstate
            var anchor = this;
            // TODO: Make expiration time configurable
            var expiration = moment.duration(7, 'days');
            navigatorApp.permalink.make_uri_opaque(viewstate, {ttl: expiration.asSeconds()}).then(function(url) {

                // v1: open url
                //$(anchor).attr('href', url);

                // v2: open permalink popover
                navigatorApp.permalink.popover_show(anchor, url, {
                    title: 'Share search',
                    intro: 'by sending a link to the current search to third-party users.',
                    ttl: expiration,
                });

            });
        });


        // Transform query: modifier kind selected in dialog
        $('.btn-clipboard-modifier').on('click', function() {

            // get field name and operator from dialog
            var modifier = $(this).data('modifier');
            var operator = $('#clipboard-modifier-operator').find('.btn.active').data('value') || 'OR';

            // close dialog
            $('#query-transform-dialog').modal('hide');

            // compute new query content
            var text = $('#query').val().trim();
            if (_.str.contains(text, '=')) {
                return;
            }
            var entries = text.split('\n').filter(function(item) { return item != '\n' && item != ''; });
            var query = _(entries).map(function(item) {
                return modifier + '=' + '"' + item + '"';
            }).join(' ' + operator + ' ');

            // set query content and focus element
            $('#query').val(query);
            $('#query').trigger('focus');

        });


        // Normalize numberlist
        $('#btn-numberlist-normalize').off('click');
        $('#btn-numberlist-normalize').on('click', function(e) {
            e.preventDefault();
            if (_this.check_numberlist_empty({'icon': 'icon-exchange'})) { return; }

            normalize_numberlist($('#numberlist').val()).then(function(response) {
                var numbers_valid = response['numbers-normalized'] && response['numbers-normalized']['valid'];
                var numbers_invalid = response['numbers-normalized'] && response['numbers-normalized']['invalid'];

                // replace numberlist in ui by normalized one
                $('#numberlist').val(numbers_valid.join('\n'));

                // display invalid patent numbers
                if (_.isEmpty(numbers_invalid)) {
                    navigatorApp.ui.notify(
                        'Patent numbers normalized successfully',
                        {type: 'success', icon: 'icon-exchange', right: true});
                } else {
                    var message = 'Number normalization failed for:<br/><br/><pre>' + numbers_invalid.join('\n') + '</pre>';
                    navigatorApp.ui.user_alert(message, 'warning');

                }
            });
        });

        // Strip kindcodes from numbers in numberlist
        $('#btn-numberlist-strip-kindcodes').off('click');
        $('#btn-numberlist-strip-kindcodes').on('click', function(e) {
            e.preventDefault();
            if (_this.check_numberlist_empty({'icon': 'icon-eraser'})) { return; }

            var numberlist = $('#numberlist').val();
            var numbers = numberlist.split('\n');
            numbers = _(numbers).map(patent_number_strip_kindcode);
            $('#numberlist').val(numbers.join('\n'));

            navigatorApp.ui.notify(
                'Stripped patent kind codes',
                {type: 'success', icon: 'icon-eraser', right: true});

        });

        // Export to patselect
        $('#btn-ps-export').off('click');
        $('#btn-ps-export').on('click', function(e) {
            e.preventDefault();
            navigatorApp.ui.work_in_progress();
        });

    },

    clear_comfort_form: function() {
        navigatorApp.metadata.dirty(true);
        $('#querybuilder-comfort-form').find('input').val('');
    },

    setup_quick_cql_builder: function() {

        // ------------------------------------------
        //   cql quick query builder
        //   NOTE: currently defunct
        // ------------------------------------------
        $('.btn-cql-boolean').button();
        $('#cql-quick-operator').find('.btn-cql-boolean').on('click', function() {
            $('#query').trigger('focus');
        });
        $('.btn-cql-field').on('click', function() {

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

            $('#query').trigger('focus');
        });

    },

    setup_datasource_button: function(datasource) {
        // Activate appropriate datasource button
        var button = this.get_datasource_button(datasource);
        button && button.button('toggle');
    },

    setup_cql_field_chooser: function(hide) {

        var _this = this;

        var datasource = navigatorApp.get_datasource();
        var datasource_info = this.get_datasource_info();
        var queryflavor = navigatorApp.queryBuilderView.get_flavor();

        var analytics_actions = $('#analytics-actions')[0]; //.previousSibling;
        if (queryflavor == 'comfort') {
            $(analytics_actions).show();
        } else {
            $(analytics_actions).hide();
        }

        // Disable field chooser
        if (hide || !datasource || queryflavor != 'cql' ||
            (datasource_info && datasource_info.querybuilder.disable_field_chooser)
            ) {
            $('#cql-field-chooser-row').hide();
            return;
        } else {
            $('#cql-field-chooser-row').show();
        }

        // Get knowledge about fields
        var fields_knowledge = FIELDS_KNOWLEDGE[datasource] || {};

        // Setup "select" widget
        $('#cql-field-chooser').select2({
            placeholder: 'Field symbols' + ' (' + datasource + ')',
            data: { results: fields_knowledge.fields },
            dropdownCssClass: "bigdrop",
            escapeMarkup: function(text) { return text; },
            width: '100%',
        });

        // Setup "onselect" event handler
        $('#cql-field-chooser').off('change');
        $('#cql-field-chooser').on('change', function(event) {

            // Only apply to "added" events, skip all others
            if (!event.added) return;

            // Get field metadata
            var fields_metadata  = fields_knowledge.meta || {};

            if (datasource_info.querybuilder.enable_syntax_chooser) {
                var form_data = _this.get_common_form_data();
                var syntax = form_data.modifiers['syntax-ikofax'] == true ? 'ikofax' : 'cql';
                fields_metadata = fields_metadata[syntax] || {};
            }

            //log('fields_metadata:', fields_metadata);


            var fieldname = $(this).val();
            if (!fieldname) return;

            var query = $('#query').val();
            var position = $('#query').caret();

            var location = fields_metadata.location || 'left';

            // Characters left and right of current cursor position
            var leftchar = query.substring(position - 1, position);
            var rightchar = query.substring(position, position + 1);

            // Insert space before new field if there is none and we're not at the beginning
            var padding = '';
            if (leftchar != ' ' && position != 0) padding = ' ';

            // Skip insert if we're right behind a "=" or right before a "/"
            if (leftchar == fields_metadata.separator || rightchar == fields_metadata.separator) {
                $('#query').trigger('focus');
                return;
            }

            // Insert field name and separator
            if (location == 'left') {
                var inject = padding + fieldname + fields_metadata.separator;
                $('#query').caret(inject);

            } else if (location == 'right') {
                var fragment = fields_metadata.separator + fieldname;
                var inject = padding + fragment;
                $('#query').caret(inject).caret(-fragment.length);

            }

            // Reset select widget
            $(this).data('select2').clear();

        });

    },

    setup_sorting_chooser: function() {

        log('setup_sorting_chooser');

        var datasource = navigatorApp.get_datasource();

        var fields_knowledge = FIELDS_KNOWLEDGE[datasource] || {};


        var element_field_chooser = $('#sort-field-chooser');
        var element_order_chooser = $('#sort-order-chooser');


        // --------------------
        //   sort field
        // --------------------

        element_field_chooser.select2({
            placeholder: '<i class="icon-sort"></i> Sorting',
            data: { results: fields_knowledge.sorting },
            dropdownCssClass: "bigdrop",
            escapeMarkup: function(text) { return text; },
        });

        element_field_chooser.off('change');
        element_field_chooser.on('change', function(event) {

            var value = $(this).val();
            if (!value) return;

            var sort_order = element_order_chooser.data('value');
            if (!sort_order) {
                element_order_chooser.trigger('click');
            }

        });


        // --------------------
        //   sort order
        // --------------------

        function sort_order_refresh() {

            //log('sort_order_refresh');

            // read from "data-value" attribute
            var value = element_order_chooser.data('value');

            // compute and set proper icon class
            var icon_class = 'icon-sort';
            if (value == 'asc') {
                icon_class = 'icon-sort-down';
            } else if (value == 'desc') {
                icon_class = 'icon-sort-up';
            }
            element_order_chooser.find('i').attr('class', icon_class);
        }
        sort_order_refresh();

        element_order_chooser.off('click');
        element_order_chooser.on('click', function(event) {

            // read from "data-value" attribute
            var value = $(this).data('value');

            //log('value-before:', value);

            // sort order state machine
            if (!value) {
                value = 'asc';
            } else if (value == 'asc') {
                value = 'desc';
            } else if (value == 'desc') {
                value = null;
            }

            //log('value-after: ', value);

            // store in "data-value" attribute
            $(this).data('value', value);

            sort_order_refresh();

        });

    },

    cql_history_chooser_get_data: function() {

        var deferred = $.Deferred();

        if (!navigatorApp.project) {
            var message = 'Project subsystem not started. Query history not available.';
            console.warn(message);
            navigatorApp.ui.notify(message, {type: 'warning', icon: 'icon-time'});
            deferred.reject();
            return deferred.promise();
        }

        log('cql_history_chooser_get_data: begin');

        // fetch query objects and sort descending by creation date
        var _this = this;
        $.when(navigatorApp.project.fetch_queries()).then(function() {
            var query_collection = navigatorApp.project.get('queries');
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

        /*
        var queries = navigatorApp.project.get('queries');
        var chooser_data = _(queries).unique().map(function(query) {
            return { id: query, text: query };
        });
        return chooser_data;
        */
    },

    query_model_repr: function(query) {


        // ------------------------------------------
        // Crunch some data for query history display
        // ------------------------------------------

        var flavor = query.get('flavor');
        var datasource = query.get('datasource');
        var query_data = query.get('query_data');
        var query_expert = query.get('query_expert');
        var created = query.get('created');
        var result_count = query.get('result_count');

        // Backward compatibility
        if (datasource == 'ifi') {
            datasource = 'ificlaims';
        }

        var datasource_info = navigatorApp.datasource_info(datasource);

        // Use query expression as title
        var expression = '';

        // TODO: Rename to "expert"
        if (flavor == 'cql') {
            if (query_expert) {
                var parts = [query_expert.expression];
                if (query_expert.filter) {
                    parts.push(query_expert.filter);
                }
                expression = parts.join(', ');
            } else {
                // Backward compatibility
                expression = query.get('query_expression');
            }
        }

        // Add serialized representation of fulltext modifiers
        var enable_fulltext_modifiers = flavor == 'comfort' || this.get_datasource_info().querybuilder.enable_fulltext_modifiers;
        if (enable_fulltext_modifiers && query_data && _.isObject(query_data['criteria'])) {
            // serialize query_data criteria
            var entries = _.map(query_data['criteria'], function(value, key) {
                // Either add "all(modifiers) == true" or individual modifiers
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
            expression = entries.join(', ');
        }

        // -----------------------------------------
        // Humanize values for query history display
        // -----------------------------------------

        // Item date
        created = moment(created).fromNow();

        // Search flavor
        var flavor_title = flavor;
        if (flavor == 'comfort') {
            flavor_title = 'Comfort';

        // TODO: Rename from "cql" to "expert"
        } else if (flavor == 'cql') {
            flavor_title = 'Expert';
        }

        // Title and color for data source label
        var datasource_label_title = datasource;
        var datasource_label_color_class = 'default';
        if (datasource_info) {
            datasource_label_title = datasource_info.title || datasource_label_title;
            datasource_label_color_class = datasource_info.querybuilder.history_label_color || datasource_label_color_class;
        }

        // Result count
        var hits_title =
            (result_count ? Humanize.compactInteger(result_count, 1) : 'no') +
                (result_count == 1 ? ' hit' : ' hits');

        // Search modifiers
        var syntax_label;
        var tags_html = [];
        if (_.isObject(query_data) && _.isObject(query_data['modifiers'])) {

            // Modifiers for OPS
            if (query_data['modifiers']['full-cycle']) {
                tags_html.push(this.html_history_tag('Full cycle', {name: 'fc', width: 'narrow'}));
            }
            if (query_data['modifiers']['family-swap-ger']) {
                tags_html.push(this.html_history_tag('Family member by priority', {name: 'fam:sw-ger', width: 'wide'}));
            }
            if (query_data['modifiers']['first-pub']) {
                tags_html.push(this.html_history_tag('First pub.', {name: 'pf', width: 'narrow'}));
            }
            if (query_data['modifiers']['recent-pub']) {
                tags_html.push(this.html_history_tag('Recent pub.', {name: 'rf', width: 'narrow'}));
            }

            // Modifier for "Expression syntax"
            // TODO: Rename from "cql" to "expert"
            if (flavor == 'cql') {
                //syntax_label = 'CQL';
                if (query_data['modifiers']['syntax-ikofax']) {
                    syntax_label = 'Ikofax';
                }
            }

            // Modifier for "Remove family members"
            if (query_data['modifiers']['family-remove']) {
                tags_html.push(this.html_history_tag('Remove family members', {name: '-fam:rm', width: 'wide'}));
            }

            // Modifier for "Replace family members"
            if (query_data['modifiers']['family-replace']) {
                tags_html.push(this.html_history_tag('Replace family members', {name: '-fam:rp', width: 'wide'}));
            }

            // Modifier for "Expand family members"
            if (query_data['modifiers']['family-full']) {
                tags_html.push(this.html_history_tag('Full family', {name: '+fam', width: 'narrow'}));
            }

        }

        // Sorting control
        if (_.isObject(query_data) && _.isObject(query_data['sorting'])) {
            tags_html.push(query_data.sorting.field + ':' + query_data.sorting.order);
        }

        // ------------------------------------------
        //               Generate HTML
        // ------------------------------------------

        // Left side
        var hits_bs =
            '<small/>' +
            this.html_history_tag(hits_title, {role: 'hits', type: 'badge', kind: result_count > 0 ? 'success' : 'default'}) +
            '</small>';
        var row1_left_side = [this.html_history_expression(expression)];
        var row2_left_side = [this.html_history_expression(hits_bs)];


        // Right side

        // Bootstrapify labels
        var history_header = [];
        history_header.push(this.html_history_tag(created, {type: 'text'}));
        syntax_label && history_header.push(this.html_history_tag(syntax_label, {role: 'flavor'}));
        history_header.push(this.html_history_tag(flavor_title, {role: 'flavor'}));
        history_header.push(this.html_history_tag(datasource_label_title, {role: 'datasource', kind: datasource_label_color_class}));

        // The whole entry
        var row1_right_side = history_header;
        var row2_right_side = tags_html;
        var entry_html =
            '<div class="container-fluid history-container">' +
            '<div class="row-fluid history-row-1">' + row1_left_side.join('') + this.html_history_labels(row1_right_side.join('')) + '</div>' +
            '<div class="row-fluid history-row-2">' + row2_left_side.join('') + this.html_history_labels(row2_right_side.join('')) + '</div>' +
            '</div>';
        var entry = {
            id: query,
            text: entry_html,
        };

        return entry;

    },

    html_history_expression: function(content) {
        return '<div class="span6 history-entry-expression">' + content + '</div>';
    },

    html_history_labels: function(content) {
        return '<div class="span6 history-entry-labels"><small>' + content + '</small></div>';
    },

    html_history_tag: function(content, options) {
        options = options || {};
        options.type = options.type || 'label';
        options.kind = options.kind || 'default';
        var classes = [
            options.type,
            options.type + '-' + options.kind,
            options.role  ? 'history-tag-' + options.role : '',
            options.width ? 'history-tag-' + options.width : '',
        ];
        return '<span class="' + classes.join(' ') + '">' + content + '</span>';
    },

    cql_history_chooser_setup: function() {

        var deferred = $.Deferred();

        var chooser_widget = $('#cql-history-chooser-select2');

        // Initialize empty cql history chooser widget
        this.cql_history_chooser_load_data();

        // When query was selected, put it into cql query input field
        var _this = this;
        chooser_widget.off('change');
        chooser_widget.on('change', function(event) {

            $(this).off('change');

            // This gets the "id" attribute of an entry in select2 `data`
            var query_object = $(this).val();

            // Transfer history data to current querybuilder state
            if (query_object) {

                var flavor = query_object.get('flavor');
                if (flavor == 'cql') {
                    _this.disable_compute_comfort_query = true;
                }
                _this.set_flavor(flavor);

                navigatorApp.set_datasource(query_object.get('datasource'));

                if (flavor == 'comfort') {

                    _this.clear_comfort_form();
                    _this.clear_common_form_data();

                    var data = query_object.get('query_data');
                    _this.set_comfort_form_data(data);
                    _this.set_common_form_data(data);

                } else if (flavor == 'cql') {
                    log('history cql - query_object:', query_object);

                    _this.clear_comfort_form();
                    _this.clear_common_form_data();

                    var query_expert = query_object.get('query_expert');
                    if (query_expert && query_expert.expression) {
                        $('#query').val(query_expert.expression);
                        $('#cql-filter').val(query_expert.filter);
                    } else {
                        // Backward compatibility
                        $('#query').val(query_object.get('query_expression'));
                        $('#cql-filter').val('');
                    }

                    var data = query_object.get('query_data');
                    _this.set_common_form_data(data);
                }

            }

            // Destroy widget and close dropdown container
            _this.cql_history_chooser_destroy($(this));

        });

        // load query history data and propagate to history chooser
        this.cql_history_chooser_get_data().then(function(data) {
            _this.cql_history_chooser_load_data(data);
            deferred.resolve();
        }).fail(function(event) {
            deferred.reject();
            _this.cql_history_chooser_destroy($(chooser_widget));
        });

        return deferred.promise();

    },

    cql_history_chooser_destroy: function(element) {
        // Destroy widget and close dropdown container
        element.data('select2').destroy();
        element.dropdown().toggle();
        //element.closest('#cql-history-chooser-container').hide();
    },

    cql_history_chooser_load_data: function(data) {
        var chooser_widget = $('#cql-history-chooser-select2');
        chooser_widget.select2({
            dropdownCssClass: "bigdrop history-dropdown",
            escapeMarkup: function(text) { return text; },
            data: (data || { results: [] }),
        });
    },

    setup_common_form: function() {
        var container = $('#querybuilder-area');
        var datasource_info = this.get_datasource_info();

        // Display button "(Remove|Replace) family members" only for certain search backends
        var button_family_remove         = container.find("button[id='btn-family-remove']");
        var button_family_remove_replace = container.find("button[id='btn-family-remove'],button[id='btn-family-replace']");

        // Display mode button "Replace family members"
        if (datasource_info.querybuilder.enable_remove_replace_family_members) {
            button_family_remove_replace.show();
        } else {
            button_family_remove_replace.hide();
        }

        // Display mode button "Remove family members"
        if (datasource_info.querybuilder.enable_remove_family_members) {
            button_family_remove.show();
        }

        // Display mode button "Expand family members"
        var button_family_full = container.find("button[id='btn-family-full']");
        if (datasource_info.querybuilder.enable_expand_family_members) {
            button_family_full.show();
        } else {
            button_family_full.hide();
        }

        // Display sorting widget
        if (datasource_info.querybuilder.enable_sorting) {
            $('#sorting-chooser').show();
            this.setup_sorting_chooser();
        } else {
            $('#sorting-chooser').hide();
        }

        // Display CQL filter
        if (datasource_info.querybuilder.enable_separate_filter_expression) {
            $('#cql-filter-container').show();
        } else {
            $('#cql-filter-container').hide();
        }

        // Display syntax chooser
        if (datasource_info.querybuilder.enable_syntax_chooser) {
            $('#syntax-modifier-chooser').show();
        } else {
            $('#syntax-modifier-chooser').hide();
        }

    },

    setup_comfort_form: function() {
        var form = $('#querybuilder-comfort-form');
        var datasource_info = this.get_datasource_info();
        var extra_fields = datasource_info.querybuilder.extra_fields || [];
        var placeholder = datasource_info.querybuilder.placeholder || {};

        var _this = this;

        // Fix submit by enter for internet explorer
        form.handle_enter_keypress();

        /*
        var fieldset = $('#querybuilder-comfort-form input');
        $.each(fieldset, function(index, element) {
            log('fieldset-element:', element.name);
        });
        */

        // Display some query fields conditionally
        var optional_fields = ['pubdate', 'appdate', 'priodate', 'citation'];
        _.each(optional_fields, function(fieldname) {
            var field = form.find("input[name='" + fieldname + "']");
            var container = field.closest("div[class='control-group']");
            if (_(extra_fields).contains(fieldname)) {
                field.prop('disabled', false);
                container.show();
            } else {
                field.prop('disabled', true);
                container.hide();
            }
        });

        // Adjust placeholder values for certain data sources
        function enable_placeholder(name) {

            // 1. Acquire DOM element
            var element = form.find("input[name='" + name + "']");

            // 2. Save current placeholder as default one
            if (!element.data('placeholder-default')) {
                element.data('placeholder-default', element.attr('placeholder'))
            }

            // 3. Activate placeholder based on data source
            if (placeholder[name]) {
                enable_placeholder_element(element, placeholder[name]);
            } else {
                enable_placeholder_element(element, 'default');
            }

        }
        function enable_placeholder_element(element, kind) {
            element.attr('placeholder', element.data('placeholder-' + kind));
        }

        enable_placeholder('patentnumber');
        enable_placeholder('inventor');
        enable_placeholder('class');


        // Enrich form fields with actions
        _.each(form.find(".input-prepend"), function(item) {

            // Populate field value with placeholder value on demand
            $(item).find('.add-on.add-on-label').on('click', function(ev) {
                var input_element = $(item).find('input');
                if (!input_element.val()) {

                    // Activate placeholder
                    var demo_value = input_element.attr('placeholder');
                    if (input_element.data('demo')) {
                        demo_value = input_element.data('demo');
                    }
                    input_element.val(demo_value);

                    // When data was modified, mark state as dirty
                    navigatorApp.metadata.dirty(true);

                }
            });

            // Zoom input field to textarea
            $(item).find('.add-on.add-on-zoom').on('click', function(ev) {
                var input_element = $(item).find('input');
                _this.comfort_form_regular_to_zoomed(input_element);
            });
        });

        // Conditionally display fulltext-modifier-chooser
        if (datasource_info.querybuilder.enable_fulltext_modifiers) {
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
        textarea.trigger('focus');

        navigatorApp.hotkeys.querybuilder_zoomed_hotkeys(textarea, input_element);
        navigatorApp.hotkeys.querybuilder_hotkeys(textarea);

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
        input_element && input_element.trigger('focus');
    },

    get_form_modifier_elements: function() {
        var datasource = navigatorApp.get_datasource();
        var datasource_info = navigatorApp.datasource_info(datasource);
        var modifier_buttons_selector = 'button[data-name="full-cycle"],[data-name="family-swap-ger"]';
        modifier_buttons_selector += ',[data-name="first-pub"]';
        modifier_buttons_selector += ',[data-name="recent-pub"]';

        if (datasource_info) {
            if (datasource_info.querybuilder.enable_remove_replace_family_members) {
                modifier_buttons_selector += ',[data-name="family-remove"]';
                modifier_buttons_selector += ',[data-name="family-replace"]';
            }
            if (datasource_info.querybuilder.enable_remove_family_members) {
                modifier_buttons_selector += ',[data-name="family-remove"]';
            }
            if (datasource_info.querybuilder.enable_expand_family_members) {
                modifier_buttons_selector += ',[data-name="family-full"]';
            }
            if (datasource_info.querybuilder.enable_syntax_chooser) {
                modifier_buttons_selector += ',[data-name="syntax-cql"]';
                modifier_buttons_selector += ',[data-name="syntax-ikofax"]';
            }
        }

        var elements = $('#querybuilder-area').find(modifier_buttons_selector);
        return elements;
    },

    get_common_form_data: function() {
        var flavor = this.get_flavor();
        var datasource = navigatorApp.get_datasource();

        var modifier_elements = this.get_form_modifier_elements();
        var modifiers = this.radios.get_state(modifier_elements);
        var sorting = this.collect_sorting_state_from_ui();

        var form_data = {
            format: flavor,
            datasource: datasource,
            modifiers: modifiers,
            //query: navigatorApp.config.get('query'),
        };

        if (sorting) {
            form_data.sorting = sorting;
        }

        return form_data;
    },

    set_common_form_data: function(data, options) {

        options = options || {};
        var _this = this;

        // Populate query modifiers to user interface
        // FIXME: This currently doesn't account for resetting of buttons
        //        not having a corresponding representation in "data".
        var modifier_elements = this.get_form_modifier_elements();

        _.each(modifier_elements, function(element) {
            var name = $(element).data('name');

            if (data && data.modifiers && data.modifiers[name]) {

                var activate = false;

                // Populate scalar modifiers
                if (_.isBoolean(data.modifiers[name])) {
                    if (data.modifiers[name]) {
                        activate = true;
                    }

                // Populate nested modifiers
                } else if (_.isObject(data.modifiers[name])) {

                    var element_modifier = $(element).data('modifier');
                    if (data.modifiers[name][element_modifier]) {
                        activate = true;
                    }

                }

                if (activate) {
                    $(element).addClass('active');
                    $(element).addClass('btn-info');
                } else {
                    $(element).removeClass('active');
                    $(element).removeClass('btn-info');
                }

            }

            // Set label text to default
            _this.radios.label_behaviour(element, true);

        });

        _.each(modifier_elements, function(element) {
            var is_active = $(element).hasClass('active');
            if (is_active) {
                // set label text to selected one
                _this.radios.label_behaviour(element, false);
            }
        });


        // populate sorting state to user interface
        if (data && data.sorting) {
            //log('data.sorting:', data.sorting);
            $('#sort-field-chooser').select2("val", data.sorting.field);
            $('#sort-order-chooser').data('value', data.sorting.order);
            this.setup_sorting_chooser();
        } else {
            $('#sort-field-chooser').select2("val", null);
            $('#sort-order-chooser').data('value', null);
            this.setup_sorting_chooser();
        }

    },

    clear_common_form_data: function() {

        var modifier_elements = this.get_form_modifier_elements();

        _.each(modifier_elements, function(element) {
            $(element).removeClass('active');
            $(element).removeClass('btn-info');
        });

    },

    get_comfort_form_data: function() {

        // 1. Collect search criteria from comfort form input fields
        var criteria = {};
        var form = $('#querybuilder-comfort-form');
        var fields = $(form).find('input');
        _.each(fields, function(field) {

            // Skip disabled or empty form fields
            if ($(field).prop('disabled') || !field.value) return;

            // Use field value as query criteria
            criteria[field.name] = field.value;
        });

        // Skip if collected criteria is empty
        if (_.isEmpty(criteria)) {
            return;
        }

        // 2. Collect modifiers from user interface
        var buttons = $('#querybuilder-area').find($('button[data-name="fulltext"]'));
        var modifiers = this.radios.get_state(buttons);

        var payload = this.get_common_form_data();

        var payload_local = {
            criteria: criteria,
            modifiers: modifiers,
        };

        // Merge common- and comfort-form-data
        $.extend(true, payload, payload_local);
        //log('========= payload:', payload);

        return payload;

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

    collect_sorting_state_from_ui: function() {
        var sort_state;

        var datasource = navigatorApp.get_datasource();

        var datasource_info = this.get_datasource_info();
        if (datasource_info.querybuilder.enable_sorting) {
            var field_chooser = $('#querybuilder-area').find('#sort-field-chooser');
            var order_chooser = $('#querybuilder-area').find('#sort-order-chooser');
            sort_field = field_chooser.val();
            sort_order = order_chooser.data('value');
            if (sort_field && sort_order) {
                sort_state = {
                    field: sort_field,
                    order: sort_order,
                };
            }
        }

        //log('sorting state:', sort_state);

        return sort_state;

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

        log('Comfort form criteria:', JSON.stringify(payload));

        //$("#query").val('');
        $("#keywords").val('[]');
        return this.compute_query_expression(payload).then(function(data, keywords) {
            log('Expert query data:', JSON.stringify(data));
            $("#query").val(data['expression']);
            $("#cql-filter").val(data['filter']);
            $("#keywords").val(keywords);

            // Disable Ikofax syntax
            $('#mode-syntax-buttons button').removeClass('active').removeClass('btn-info');

        }).fail(function() {
            console.warn('Failed computing query expression from:', payload);
            $("#query").val('');
            $("#keywords").val('');
            navigatorApp.ui.reset_content({documents: true, keep_notifications: true});
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
            data: JSON.stringify(payload),
            contentType: "application/json; charset=utf-8",
        }).done(function(data, status, jqXHR) {
            if (data) {
                var keywords = jqXHR.getResponseHeader('X-PatZilla-Query-Keywords');
                deferred.resolve(data, keywords);
            } else {
                deferred.resolve({}, '[]');
            }
        }).fail(function(xhr, status, reason) {
            console.error({location: 'compute_query_expression', xhr: xhr, reason: reason, status: status});
            navigatorApp.ui.propagate_backend_errors(xhr);
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

            navigatorApp.perform_numberlistsearch();
        }
    },

});


// setup component
navigatorApp.addInitializer(function(options) {

    this.listenToOnce(this, 'application:init', function() {
        this.queryBuilderView = new QueryBuilderView({});
        this.queryBuilderRegion.show(this.queryBuilderView);
    });

    // Special bootstrap handling for numberlist=EP666666,EP666667:
    this.listenTo(this, 'application:ready', function() {
        var numberlist_raw = this.config.get('numberlist');
        if (numberlist_raw) {
            var numberlist = decodeURIComponent(numberlist_raw);
            this.queryBuilderView.set_numberlist(numberlist);
        }
    });

});
