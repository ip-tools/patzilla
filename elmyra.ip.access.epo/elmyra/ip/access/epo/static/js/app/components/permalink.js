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
    permalink: function(params) {
        var deferred = $.Deferred();
        var path_url = opsChooserApp.config.get('request.path_url');
        var projectname = opsChooserApp.project.get('name');
        this.dataurl().then(function(dataurl) {
            _(params).extend({
                project: projectname,
                database: dataurl,
            });
            var url = path_url + '?' + jQuery.param(params);
            deferred.resolve(url);
        });
        return deferred.promise();
    },

    // generate an opaque permalink to the current state (project)
    permalink_opaque: function(params) {
        var deferred = $.Deferred();
        var path_url = opsChooserApp.config.get('request.path_url');

        // when generating review-in-liveview-with-ttl links on patentsearch,
        // let's view them on a pinned domain "patentview.elmyra.de"
        var host = opsChooserApp.config.get('request.host');
        if (host == 'patentsearch.elmyra.de') {
            path_url = 'https://patentview.elmyra.de/';
        }

        // compute opaque parameter variant of permalink parameters
        this.permalink(params).then(function(url) {
            opaque_param(url).then(function(opaque_query) {
                var opaqueurl = path_url + '?' + opaque_query;
                deferred.resolve(opaqueurl);
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

    popover_toggle: function(element) {
        $(element).popover('toggle');

        // focus permalink text input element and select text
        var popover_active = $(element).popover().data('popover').$tip.hasClass('in');
        if (popover_active) {
            $('#permalink-uri').select();
        }
    },

    get_textinput: function(uri) {
        var html =
            '<input id="permalink-uri" type="text" value="' + uri + '"></input>' +
                '<br/>' +
                '<small>Please copy the link above for sharing.</small>'
        return html;
    },

    setup_ui: function() {

        var _this = this;

        // simple permalink
        $('.permalink-review-liveview').unbind('click');
        $('.permalink-review-liveview').on('click', function(e) {

            // provide callback function to generate permalink uri in this scope
            var permalink_uri = undefined;
            function get_permalink() {
                return _this.get_textinput(permalink_uri);
            }

            // switch from info popover (button not yet pressed) to popover offering the permalink uri
            _this.popover_switch(this, get_permalink);

            // generate permalink uri and toggle popover
            var _button = this;
            _this.permalink({mode: 'liveview', context: 'viewer', datasource: 'review'}).then(function(url) {

                // v1: open permalink
                //window.open(url);

                // v2: show permalink
                permalink_uri = url;
                _this.popover_toggle(_button);
            });
        });

        // signed permalink with time-to-live
        $('.permalink-review-liveview-ttl').unbind('click');
        $('.permalink-review-liveview-ttl').on('click', function(e) {

            // provide callback function to generate permalink uri in this scope
            var permalink_uri = undefined;
            function get_permalink() {
                return _this.get_textinput(permalink_uri);
            }

            // switch from info popover (button not yet pressed) to popover offering the permalink uri
            _this.popover_switch(this, get_permalink);

            // generate permalink uri and toggle popover
            var _button = this;
            _this.permalink_opaque({mode: 'liveview', context: 'viewer', datasource: 'review'}).then(function(url) {

                // v1: open permalink
                //window.open(url);

                // v2: show permalink
                permalink_uri = url;
                _this.popover_toggle(_button);
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
