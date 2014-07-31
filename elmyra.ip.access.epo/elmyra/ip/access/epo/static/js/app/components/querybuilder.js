// -*- coding: utf-8 -*-
// (c) 2014 Andreas Motl, Elmyra UG

QueryBuilderView = Backbone.Marionette.ItemView.extend({

    template: "#querybuilder-template",

    initialize: function() {
        console.log('QueryBuilderView.initialize');
        //this.listenTo(this.model, "change", this.render);
        this.listenTo(this, "item:rendered", this.setup_ui);
        this.config = this.templateHelpers.config = opsChooserApp.config;
        //this.setup_ui();
    },

    templateHelpers: {},

    setup_ui: function() {
        console.log('QueryBuilderView.setup_ui');

        var _this = this;

    },

    onDomRefresh: function() {
        console.log('QueryBuilderView.onDomRefresh');
        var _this = this;

        $('#querybuilder-flavor-chooser').on('click', '.btn', function(event) {
            var flavor = $(this).data('value');

            // show/hide cql field chooser
            cql_field_chooser_setup(flavor != 'cql');

            // application action: perform search
            // properly wire "send query" button
            $('.btn-query-perform').unbind('click');
            if (flavor == 'comfort') {
                $('.btn-query-perform').click(function() {
                    $( "#querybuilder-comfort-form" ).submit();
                });

            } else if (flavor == 'cql') {
                _this.compute_comfort_query();
                $('.btn-query-perform').click(function() {
                    opsChooserApp.perform_search({reviewmode: false});
                });
            }
        });

        $( "#querybuilder-comfort-form" ).submit(function( event ) {
            event.preventDefault();
            _this.compute_comfort_query();
            //$("#querybuilder-flavor-chooser button[data-flavor='cql']").tab('show');
            opsChooserApp.perform_search();
        });

        // perform search default action
        $('.btn-query-perform').unbind('click');
        $('.btn-query-perform').click(function() {
            $( "#querybuilder-comfort-form" ).submit();
        });

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
        };

        this.query_api(payload).then(function(cql) {
            $("#query").val(cql);
        });
    },

    query_api: function(payload) {
        var deferred = $.Deferred();
        $.ajax({
            method: 'post',
            url: '/api/cql',
            async: false,
            sync: true,
            data: JSON.stringify(payload),
            contentType: "application/json; charset=utf-8",
        }).success(function(payload) {
            if (payload) {
                deferred.resolve(payload);
            }
        }).error(function(error) {
            console.warn('Error while computing cql query', error);
            deferred.reject(error);
        });
        return deferred.promise();
    },

    get_flavor: function() {
        var flavor = $('#querybuilder-flavor-chooser > .btn.active').data('value');
        return flavor;
    },

});
