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

        params = params || {};

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
        var baseurl = opsChooserApp.config.get('baseurl');

        this.permalink_params(params).then(function(params_computed) {
            var permalink = baseurl + '?' + jQuery.param(params_computed);
            deferred.resolve(permalink);
        });
        return deferred.promise();
    },

    // generate an opaque permalink to the current state (project)
    permalink_uri_opaque: function(params) {
        var deferred = $.Deferred();
        var baseurl = opsChooserApp.config.get('baseurl');

        // when generating review-in-liveview-with-ttl links on patentsearch,
        // let's view them on a pinned domain "patentview.elmyra.de"
        var host = opsChooserApp.config.get('request.host');
        if (host == 'patentsearch.elmyra.de') {
            baseurl = 'https://patentview.elmyra.de/';
        }

        // compute opaque parameter variant of permalink parameters
        this.permalink_params(params).then(function(params_computed) {
            opaque_param(params_computed).then(function(params_opaque) {
                var permalink = baseurl + '?' + params_opaque;
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

    // setup permalink popover
    popover_toggle: function(element, uri, options) {

        options = options || {};

        // toggle tip
        $(element).popover('toggle');

        // get popover tip, that is the visible overlay
        var tip = $(element).popover().data('popover').$tip;

        // check if popover tip is active
        var popover_active = tip.hasClass('in');
        if (popover_active) {
            if (uri) {

                // set the uri
                $(tip).find('#permalink-uri').val(uri);

                // open permalink on click
                $(tip).find('#permalink-open').unbind('click');
                $(tip).find('#permalink-open').click(function(e) {
                    e.preventDefault();
                    window.open(uri);
                });

                // copy permalink to clipboard
                var clipboard_button = $(tip).find('#permalink-copy')[0];
                var zeroclipboard = new ZeroClipboard(clipboard_button);
                zeroclipboard.on('ready', function(readyEvent) {

                    // intercept the copy event to set custom data
                    zeroclipboard.on('copy', function(event) {
                        var clipboard = event.clipboardData;
                        clipboard.setData('text/plain', uri);
                    });

                    // when content was copied to clipboard, notify user
                    zeroclipboard.on('aftercopy', function(event) {
                        // `this` === `client`
                        // `event.target` === the element that was clicked
                        //event.target.style.display = "none";
                        var message = "Copied permalink to clipboard, size is " + Math.round(event.data['text/plain'].length / 1000) + 'kB.';
                        $(tip).find('#permalink-message').qnotify(message, {success: true});
                    });
                });
            }

            // focus permalink text input element and select text
            $(tip).find('#permalink-uri').select();

            // show ttl message if desired
            if (options.ttl) {
                $(tip).find('#ttl-24').show();
            }
        }
    },

    get_popover_content: function() {
        var html = _.template($('#permalink-popover-template').html());
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
                _this.popover_toggle(_button, url, {ttl: true});
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
