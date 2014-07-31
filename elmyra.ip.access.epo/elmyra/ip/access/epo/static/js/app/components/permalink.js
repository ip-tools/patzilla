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

    // build query parameters
    // TODO: refactor this elsewhere, e.g. some UrlBuilder?
    query_parameters: function(params, uri) {

        params = params || {};
        uri = uri || window.location.href;

        var params_computed = {};

        // collect parameters from url
        var url = $.url(uri);
        _(params_computed).extend(url.param());

        // merge / overwrite with local params
        _(params_computed).extend(params);

        // clear parameters having empty values
        params_computed = _.objRejectEmpty(params_computed);

        return params_computed;
    },

    // build query parameters to view state
    // TODO: refactor this elsewhere, e.g. some UrlBuilder?
    query_parameters_viewstate: function(uri) {

        // aggregate parameters comprising viewer state, currently a 4-tuple
        // see also config.js:history_pushstate
        var config = opsChooserApp.config;
        var state = {
            mode: config.get('mode'),
            context: config.get('context'),
            project: config.get('project'),
            datasource: config.get('datasource'),
        };

        // remove parameters which do not differ from their default
        _.each(state, function(value, key) {
            if (config._originalAttributes[key] == value) {
                delete state[key];
            }
        }, this);

        var params_computed = this.query_parameters(state, uri);

        return params_computed;
    },

    // build an url to self
    // TODO: refactor this elsewhere, e.g. some UrlBuilder?
    make_uri: function(params) {
        var baseurl = opsChooserApp.config.get('baseurl');
        var permalink = baseurl + '?' + jQuery.param(this.query_parameters(params));
        return permalink;
    },

    // build an opaque parameter permalink with expiration
    make_uri_opaque: function(params) {
        var deferred = $.Deferred();
        var baseurl = opsChooserApp.config.get('baseurl');

        // when generating review-in-liveview-with-ttl links on patentsearch,
        // let's view them on a pinned domain like "patentview.elmyra.de"
        var host = opsChooserApp.config.get('request.host');
        if (_.string.contains(host, 'patentsearch')) {
            baseurl = baseurl.replace('patentsearch', 'patentview');
        }

        // compute opaque parameter variant of permalink parameters
        var params_computed = this.query_parameters(params);
        opaque_param(params_computed).then(function(params_opaque) {
            var permalink = baseurl + '?' + params_opaque;
            deferred.resolve(permalink);
        });

        return deferred.promise();
    },

    popover_switch: function(element, content, options) {
        // destroy original popover and replace with permalink popover

        options = options || {};

        var popover = $(element).popover();
        if (popover.data('amended')) return;

        popover.data('amended', true);
        var title = options.title || popover.data('content');
        $(element).popover('destroy');
        $(element).popover({
            title: title,
            content: content,
            html: true,
            placement: 'bottom',
            trigger: 'manual'});
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

                // TODO: refactor to seperate function

                // set the intro text
                if (options.intro) {
                    var intro_html = options.intro;
                    $(tip).find('#permalink-popover-intro').html(intro_html);
                }

                // popover-container

                // set the uri
                $(tip).find('#permalink-uri-textinput').val(uri);

                // open permalink on click
                $(tip).find('#permalink-open').unbind('click');
                $(tip).find('#permalink-open').click(function(e) {
                    e.preventDefault();
                    window.open(uri);
                });

                // prevent default action on copy button
                $(tip).find('#permalink-copy').unbind('click');
                $(tip).find('#permalink-copy').click(function(e) {
                    e.preventDefault();
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
                        $(tip).find('#permalink-popover-message').qnotify(message, {success: true});
                    });
                });

                // apply more generic augmentations
                opsChooserApp.ui.setup_text_tools();

            }

            // focus permalink text input element and select text
            $(tip).find('#permalink-uri-textinput').select();

            // show ttl message if desired
            if (options.ttl) {
                $(tip).find('#ttl-24').show();
            }
        }
    },

    popover_get_content: function() {
        var html = _.template($('#permalink-popover-template').html());
        return html;
    },

    popover_show: function(element, url, options) {

        // switch from info popover (button not yet pressed) to popover offering the permalink uri
        this.popover_switch(element, this.popover_get_content, options);

        // show permalink overlay
        this.popover_toggle(element, url, options);

    },

    liveview_with_database_params: function() {

        var deferred = $.Deferred();

        // TODO: what about propagating the "context"?
        var projectname = opsChooserApp.project.get('name');
        // TODO: use in future: var projectname = opsChooserApp.config.get('project');

        var params = {
            mode: 'liveview',
            context: 'viewer',
            project: projectname,
            query: undefined,
            datasource: 'review',
        };
        this.dataurl().then(function(dataurl) {
            _(params).extend({
                database: dataurl,
            });
            deferred.resolve(params);
        });

        return deferred.promise();
    },

    // TODO: refactor elsewhere, e.g. to LinkBuilder.setup_project_buttons
    setup_ui: function() {

        var _this = this;

        // simple permalink
        $('.permalink-review-liveview').unbind('click');
        $('.permalink-review-liveview').on('click', function(e) {

            // generate permalink uri and toggle popover
            var _button = this;
            _this.liveview_with_database_params().then(function(params) {

                // compute permalink
                var url = _this.make_uri(params);

                e.preventDefault();
                e.stopPropagation();

                // show permalink overlay
                _this.popover_show(_button, url, {
                    intro:
                        '<small>' +
                            'This offers a persistent link to review the current project. ' +
                            'It will transfer the whole project structure including queries and basket content with rating scores.' +
                        '</small>',
                });

            });
        });

        // signed permalink with time-to-live
        $('.permalink-review-liveview-ttl').unbind('click');
        $('.permalink-review-liveview-ttl').on('click', function(e) {

            // generate permalink uri and toggle popover
            var _button = this;
            _this.liveview_with_database_params().then(function(params) {

                // compute permalink
                _this.make_uri_opaque(params).then(function(url) {

                    e.preventDefault();
                    e.stopPropagation();

                    // show permalink overlay
                    _this.popover_show(_button, url, {
                        intro:
                            '<small>' +
                                'This offers a link for external/anonymous users to review the current project. ' +
                                'It will transfer the whole project structure including queries and basket content with rating scores.' +
                            '</small>',
                        ttl: true,
                    });
                });

            });

        });

    },

});


// setup plugin
opsChooserApp.addInitializer(function(options) {

    // offer this throughout the whole application
    this.permalink = new PermalinkPlugin();

    this.listenTo(this, 'application:ready', function() {
        this.permalink.setup_ui();
    });

    this.listenTo(this, 'results:ready', function() {
        this.permalink.setup_ui();
    });

});
