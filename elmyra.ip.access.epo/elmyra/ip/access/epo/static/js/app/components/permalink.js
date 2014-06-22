// -*- coding: utf-8 -*-
// (c) 2014 Andreas Motl, Elmyra UG

PermalinkPlugin = Marionette.Controller.extend({

    initialize: function(options) {
        console.log('PermalinkPlugin.initialize');
    },

    dataurl: function() {
        // produce "data" url representation like "data:application/json;base64,ewogICAgImRhdGF..."
        var deferred = $.Deferred();
        opsChooserApp.storage.dump().then(function(backup) {
            var payload = JSON.stringify(backup);
            var content = dataurl.format({data: payload, mimetype: 'application/json+lz-string', charset: 'utf-8'});
            return deferred.resolve(content);
        });
        return deferred.promise();
    },

    // generate a permalink to the current state (project)
    permalink_params: function(params) {
        var deferred = $.Deferred();
        var projectname = opsChooserApp.project.get('name');
        // TODO: use in future: var projectname = opsChooserApp.config.get('project');

        var params_computed = {};

        // collect parameters from url
        var url = $.url(window.location.href);
        _(params_computed).extend(url.param());

        // merge / overwrite with local params
        _(params_computed).extend(params);

        // merge "dataurl" representation of the whole database
        this.dataurl().then(function(dataurl) {
            _(params_computed).extend({
                project: projectname,
                database: dataurl,
            });

            // clear parameters having empty values
            params_computed = _.objReject(params_computed, function(value, key) { return _.isEmpty(value); })

            deferred.resolve(params_computed);
        });
        return deferred.promise();
    },

    // generate a permalink to the current state (project)
    permalink_uri: function(params) {
        var deferred = $.Deferred();
        var path_url = opsChooserApp.config.get('request.path_url');

        this.permalink_params(params).then(function(params_computed) {
            var permalink = path_url + '?' + jQuery.param(params_computed);
            deferred.resolve(permalink);
        });
        return deferred.promise();
    },

    // generate an opaque permalink to the current state (project)
    permalink_uri_opaque: function(params) {
        var deferred = $.Deferred();
        var path_url = opsChooserApp.config.get('request.path_url');

        // when generating review-in-liveview-with-ttl links on patentsearch,
        // let's view them on a pinned domain "patentview.elmyra.de"
        var host = opsChooserApp.config.get('request.host');
        if (host == 'patentsearch.elmyra.de') {
            path_url = 'https://patentview.elmyra.de/';
        }

        // compute opaque parameter variant of permalink parameters
        this.permalink_params(params).then(function(params_computed) {
            opaque_param(params_computed).then(function(params_opaque) {
                var permalink = path_url + '?' + params_opaque;
                deferred.resolve(permalink);
            });
        });
        return deferred.promise();
    },

    popover_switch: function(element, content) {
        // destroy original popover and replace with permalink popover
        var popover = $(element).popover();
        if (!popover.data('amended')) {
            popover.data('amended', true);
            var title = popover.data('content');
            $(element).popover('destroy');
            $(element).popover({
                title: title,
                content: content,
                html: true,
                placement: 'bottom',
                trigger: 'manual'});
        }
    },

    popover_toggle: function(element, uri) {
        $(element).popover('toggle');

        // focus permalink text input element and select text
        var tip = $(element).popover().data('popover').$tip;
        var popover_active = tip.hasClass('in');
        if (popover_active) {
            if (uri) {
                $(tip).find('#permalink-uri').val(uri);
            }
            $(tip).find('#permalink-uri').select();
        }
    },

    get_popover_content: function() {
        var html =
            '<input id="permalink-uri" type="text"></input>' +
                '<br/>' +
                '<small>Please copy the link above for sharing.</small>'
        return html;
    },

    setup_ui: function() {

        var _this = this;

        // simple permalink
        $('.permalink-review-liveview').unbind('click');
        $('.permalink-review-liveview').on('click', function(e) {

            // switch from info popover (button not yet pressed) to popover offering the permalink uri
            _this.popover_switch(this, _this.get_popover_content);

            // generate permalink uri and toggle popover
            var _button = this;
            _this.permalink_uri({mode: 'liveview', context: 'viewer', datasource: 'review', query: undefined}).then(function(url) {

                // v1: open permalink
                //window.open(url);

                // v2: show permalink
                _this.popover_toggle(_button, url);
            });
        });

        // signed permalink with time-to-live
        $('.permalink-review-liveview-ttl').unbind('click');
        $('.permalink-review-liveview-ttl').on('click', function(e) {

            // switch from info popover (button not yet pressed) to popover offering the permalink uri
            _this.popover_switch(this, _this.get_popover_content);

            // generate permalink uri and toggle popover
            var _button = this;
            _this.permalink_uri_opaque({mode: 'liveview', context: 'viewer', datasource: 'review', query: undefined}).then(function(url) {

                // v1: open permalink
                //window.open(url);

                // v2: show permalink
                _this.popover_toggle(_button, url);
            });
        });

    },

});


// setup plugin
opsChooserApp.addInitializer(function(options) {
    this.permalink = new PermalinkPlugin();

    this.listenTo(this, 'application:ready', function() {
        this.permalink.setup_ui();
    });

    this.listenTo(this, 'results:ready', function() {
        this.permalink.setup_ui();
    });

});
