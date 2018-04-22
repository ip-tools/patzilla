// -*- coding: utf-8 -*-
// (c) 2015 Andreas Motl, Elmyra UG

AbstractResultFetcher = Marionette.Controller.extend({

    initialize: function(options) {
        options = options || {};
    },

    start: function() {
        var deferred = $.Deferred();

        var data = navigatorApp.queryBuilderView.get_comfort_form_data();
        if (!data || !data.criteria) {
            deferred.reject('Empty form data');
            return deferred;
        }

        var url = this.get_url(data);

        var _this = this;
        log('url:', url);
        $.ajax({url: url, async: true})
            .then(function(payload) {
                if (payload) {
                    deferred.resolve(payload);
                } else {
                    deferred.reject('Empty response');
                }
            }).catch(function(error) {
                console.warn('Error with AbstractResultFetcher:', error);
                deferred.reject(JSON.stringify(error));
            });
        return deferred;
    },

});

AbstractResultView = GenericResultView.extend({

    initialize: function() {
        this.fetcher_class = null;
    },

    onShow: function() {
        this.hide_buttons();
        this.start();
    },

    setup_data: function(data) {
        // transfer json payload to textarea
        $('#result-content').val(JSON.stringify(data, null, 2));
    },

    fetcher_factory: function() {
        return eval('new ' + this.fetcher_class + '()');
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

ResultAnalyticsFamilyView = AbstractResultView.extend({

    initialize: function() {
        console.log('ResultAnalyticsFamilyView.initialize');
        this.fetcher_class = 'ResultAnalyticsFamilyFetcher';
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

ResultAnalyticsDaterangeView = AbstractResultView.extend({

    initialize: function(options) {
        console.log('ResultAnalyticsDaterangeView.initialize');
        options = options || {};
        this.kind = options.kind;
    },

    onShow: function() {
        this.start();
    },

    setup_data: function(data) {

        AbstractResultView.prototype.setup_data.call(this, data);

        // transfer numberlist to button actions
        var numberlist = [];
        _.each(data, function(item) {
            item.pubnumber && numberlist.push(item.pubnumber);
            item.publication_number && numberlist.push(item.publication_number);
        });
        this.setup_numberlist_buttons(numberlist);

    },

    fetcher_factory: function() {
        return new ResultAnalyticsDaterangeFetcher({kind: this.kind});
    },

});


ResultAnalyticsDistinctApplicantFetcher = AbstractResultFetcher.extend({

    get_url: function(data) {
        var url_tpl = _.template('/api/analytics/applicants-distinct?<%= criteria_query %>&datasource=<%= datasource %>');
        var url = url_tpl({criteria_query: $.param(data.criteria), datasource: data.datasource});
        return url;
    },

});

ResultAnalyticsDistinctApplicantView = AbstractResultView.extend({

    initialize: function() {
        console.log('ResultAnalyticsDistinctApplicantView.initialize');
        this.fetcher_class = 'ResultAnalyticsDistinctApplicantFetcher';
    },

});


navigatorApp.addInitializer(function(options) {

    this.listenTo(this, 'application:ready', function() {
        var _this = this;

        var module_name = 'analytics';
        var module_available = navigatorApp.user_has_module(module_name);

        // wire fetch-results buttons
        $('#analytics-family-overview-button').off('click');
        $('#analytics-family-overview-button').on('click', function() {
            if (module_available) {
                make_modal_view(ResultAnalyticsFamilyView, _this.metadata);
            } else {
                _this.ui.notify_module_locked(module_name);
            }
        });

        $('.analytics-daterange-button').off('click');
        $('.analytics-daterange-button').on('click', function() {
            if (module_available) {
                make_modal_view(ResultAnalyticsDaterangeView, _this.metadata, {kind: $(this).data('kind')});
            } else {
                _this.ui.notify_module_locked(module_name);
            }
        });

        $('.analytics-applicants-distinct-button').off('click');
        $('.analytics-applicants-distinct-button').on('click', function() {
            if (module_available) {
                make_modal_view(ResultAnalyticsDistinctApplicantView, _this.metadata);
            } else {
                _this.ui.notify_module_locked(module_name);
            }
        });

    });

});
