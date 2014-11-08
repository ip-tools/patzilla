// -*- coding: utf-8 -*-
// (c) 2014 Andreas Motl, Elmyra UG

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
                $('#querybuilder-cql-actions').hide();

                // hide history chooser
                $('#cql-history-chooser').hide();

                // perform field-based search
                $('.btn-query-perform').click(function() {
                    $( "#querybuilder-comfort-form" ).submit();
                });

            } else if (flavor == 'cql') {

                // focus textarea
                $('#query').focus();

                // show action tools
                $('#querybuilder-cql-actions').show();

                // show history chooser
                $('#cql-history-chooser').show();
                $('#cql-history-chooser').css('display', 'inline');

                // convert query from form fields to cql expression
                _this.compute_comfort_query();

                // perform cql expression search
                $('.btn-query-perform').click(function() {
                    opsChooserApp.perform_search({reviewmode: false, clear: true});
                });
            }
        });


        // ------------------------------------------
        //   submit search
        // ------------------------------------------

        $( "#querybuilder-comfort-form" ).submit(function( event ) {
            event.preventDefault();

            // transfer values from zoomed fields
            _this.comfort_form_zoomed_to_regular_data();

            // convert query from form fields to cql expression
            _this.compute_comfort_query();

            //$("#querybuilder-flavor-chooser button[data-flavor='cql']").tab('show');
            opsChooserApp.perform_search({reviewmode: false, clear: true});
        });

        // perform search default action
        $('.btn-query-perform').unbind('click');
        $('.btn-query-perform').click(function() {
            $( "#querybuilder-comfort-form" ).submit();
        });


        // ------------------------------------------
        //   full-cycle mode chooser
        // ------------------------------------------

        // https://github.com/twbs/bootstrap/issues/2380#issuecomment-13981357
        $('.btn-full-cycle').on('click', function (e) {
            event.stopPropagation();
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

    setup_ui_actions: function() {

        var _this = this;

        // ------------------------------------------
        //   cql query area action tools
        // ------------------------------------------

        // trash icon clears the whole content
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
        var queries = opsChooserApp.project.get('queries');
        var chooser_data = _(queries).unique().map(function(query) {
            return { id: query, text: query };
        });
        return chooser_data;
    },
    cql_history_chooser_setup: function() {
        var projectname = opsChooserApp.project.get('name');
        var data = this.cql_history_chooser_get_data();

        var chooser_widget = $('#cql-history-chooser-select2');

        // initialize cql history chooser
        chooser_widget.select2({
            placeholder: 'CQL history' + ' (' + projectname + ')',
            data: { results: data },
            dropdownCssClass: "bigdrop",
            escapeMarkup: function(text) { return text; },
        });

        // when query was selected, put it into cql query input field
        chooser_widget.unbind('change');
        chooser_widget.on('change', function(event) {

            $(this).unbind('change');

            var value = $(this).val();
            if (value) {

                // HACK: cut away suffix, currently it's appended to query string => dirty :-(
                // TODO: move to QueryModel
                var datasources = ['ops', 'depatisnet', 'google', 'ftpro'];
                _(datasources).each(function(datasource) {
                    if (_.string.endsWith(value, '[' + datasource + ']') || _.string.endsWith(value, '(' + datasource + ')')) {
                        opsChooserApp.set_datasource(datasource);
                    }
                    value = value
                        .replace(' [' + datasource + ']', '').replace(' (' + datasource + ')', '')
                });

                $('#query').val(value);
            }

            // destroy widget and close dropdown container
            $(this).data('select2').destroy();
            $(this).dropdown().toggle();

        });

    },

    setup_comfort_form: function() {
        var form = $('#querybuilder-comfort-form');
        var datasource = opsChooserApp.get_datasource();

        var _this = this;

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

        // submit on meta+enter
        textarea.unbind('keydown');
        textarea.on('keydown', null, 'meta+return', function() {
            $("#querybuilder-comfort-form").submit();
        });
        textarea.on('keydown', null, 'ctrl+return', function(event) {
            $("#querybuilder-comfort-form").submit();
        });
        textarea.on('keydown', null, 'ctrl+z', function(event) {
            _this.comfort_form_zoomed_to_regular_data();
            _this.comfort_form_zoomed_to_regular_ui(input_element);
        });

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

    read_comfort_form: function(form) {
        var fields = $(form).find($('input'));
        var payload = {};
        _.each(fields, function(item) {
            if (item.value) {
                payload[item.name] = item.value;
            }
        });
        //log('payload:', JSON.stringify(payload));
        return payload;
    },

    compute_comfort_query: function() {

        var criteria = this.read_comfort_form($('#querybuilder-comfort-form'));
        var datasource = opsChooserApp.get_datasource();

        var payload = {
            format: 'comfort',
            criteria: criteria,
            datasource: datasource,
            //query: opsChooserApp.config.get('query'),
        };

        //$("#query").val('');
        $("#keywords").val('[]');
        this.compute_query_expression(payload).then(function(expression, keywords) {
            expression && $("#query").val(expression);
            keywords && $("#keywords").val(keywords);
        });
    },

    compute_query_expression: function(payload) {
        var deferred = $.Deferred();
        $.ajax({
            method: 'post',
            url: '/api/util/query-expression',
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
        }).error(function(xhr) {
            opsChooserApp.ui.propagate_alerts(xhr.responseText);
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

});
