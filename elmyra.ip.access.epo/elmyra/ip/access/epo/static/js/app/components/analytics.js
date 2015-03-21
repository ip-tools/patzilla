// -*- coding: utf-8 -*-
// (c) 2015 Andreas Motl, Elmyra UG

AbstractResultFetcher = Marionette.Controller.extend({

    start: function() {
        var deferred = $.Deferred();

        var data = opsChooserApp.queryBuilderView.get_comfort_form_data();
        if (!data || !data.criteria) {
            deferred.reject('Empty form data');
            return deferred;
        }

        var url = this.get_url(data);

        var _this = this;
        log('url:', url);
        $.ajax({url: url, async: true})
            .success(function(payload) {
                if (payload) {
                    deferred.resolve(payload);
                } else {
                    deferred.reject('Empty response');
                }
            }).error(function(error) {
                deferred.reject('API failed: ' + JSON.stringify(error));
            });
        return deferred;
    },

});

ResultAnalyticsFamilyFetcher = AbstractResultFetcher.extend({

    initialize: function(options) {
        log('ResultAnalyticsFamilyFetcher.initialize');
        options = options || {};
    },

    get_url: function(data) {
        var url_tpl = _.template('/api/analytics/family/overview?<%= criteria_query %>&datasource=<%= datasource %>');
        var url = url_tpl({criteria_query: $.param(data.criteria), datasource: data.datasource});
        return url;
    },

});

ResultAnalyticsFamilyView = GenericResultView.extend({

    initialize: function() {
        console.log('ResultAnalyticsFamilyView.initialize');
    },

    onShow: function() {
        this.hide_buttons();
        this.start();
    },

    setup_data: function(data) {

        // transfer json payload to textarea
        $('#result-content').val(JSON.stringify(data, null, 2));

        // don't setup buttons
        //this.setup_numberlist_buttons(numberlist);

    },

    fetcher_factory: function() {
        var fetcher = new ResultAnalyticsFamilyFetcher();
        return fetcher;
    },

});


ResultAnalyticsDaterangeFetcher = AbstractResultFetcher.extend({

    initialize: function(options) {
        log('ResultAnalyticsDaterangeFetcher.initialize');
        options = options || {};
        this.kind = options.kind
    },

    get_url: function(data) {
        var url_tpl = _.template('/api/analytics/daterange/<%= kind %>?<%= criteria_query %>&datasource=<%= datasource %>');
        var url = url_tpl({kind: this.kind, criteria_query: $.param(data.criteria), datasource: data.datasource});
        return url;
    },

});

ResultAnalyticsDaterangeView = GenericResultView.extend({

    initialize: function(options) {
        console.log('ResultAnalyticsDaterangeView.initialize');
        options = options || {};
        this.kind = options.kind;
    },

    onShow: function() {
        this.start();
    },

    setup_data: function(data) {

        // transfer json payload to textarea
        $('#result-content').val(JSON.stringify(data, null, 2));

        // transfer numberlist to button actions
        var numberlist = [];
        _.each(data, function(item) {
            item.pubnumber && numberlist.push(item.pubnumber);
            item.publication_number && numberlist.push(item.publication_number);
        });
        this.setup_numberlist_buttons(numberlist);

    },

    fetcher_factory: function() {
        var fetcher = new ResultAnalyticsDaterangeFetcher({kind: this.kind});
        return fetcher;
    },

});



opsChooserApp.addInitializer(function(options) {

    this.listenTo(this, 'application:ready', function() {
        var _this = this;

        var module_name = 'analytics';
        var module_available = opsChooserApp.user_has_module(module_name);

        // wire fetch-results buttons
        $('#analytics-family-overview-button').unbind('click');
        $('#analytics-family-overview-button').click(function() {
            if (module_available) {
                make_modal_view(ResultAnalyticsFamilyView, _this.metadata);
            } else {
                _this.ui.notify_module_locked(module_name);
            }
        });

        $('.analytics-daterange-button').unbind('click');
        $('.analytics-daterange-button').click(function() {
            if (module_available) {
                make_modal_view(ResultAnalyticsDaterangeView, _this.metadata, {kind: $(this).data('kind')});
            } else {
                _this.ui.notify_module_locked(module_name);
            }
        });
    });

});
