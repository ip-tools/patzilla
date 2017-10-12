// -*- coding: utf-8 -*-
// (c) 2014-2016 Andreas Motl, Elmyra UG
var dataurl = require('dataurl').dataurl;
var opaque_param = require('patzilla.navigator.components.opaquelinks').opaque_param;

PermalinkPlugin = Marionette.Controller.extend({

    initialize: function(options) {
        console.log('PermalinkPlugin.initialize');
    },

    setup_ui: function() {
        var _this = this;
    },

    dataurl: function() {
        // produce "data" url representation like "data:application/json;base64,ewogICAgImRhdGF..."
        var deferred = $.Deferred();
        navigatorApp.storage.dump().then(function(backup) {
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
    query_parameters_viewstate: function(uri, options) {

        options = options || {};

        // Aggregate parameters comprising viewer state, currently a 4-tuple
        // See also config.js:history_pushstate
        var config = navigatorApp.config;
        var state = {
            mode: config.get('mode'),
            context: config.get('context'),
            project: config.get('project'),
            datasource: config.get('datasource'),
        };

        // Add search modifiers and more to viewstate
        if (!options.no_modifiers) {
            var metadata_params = this.metadata_to_parameters();
            _.extend(state, metadata_params);
        }

        // Remove parameters which do not differ from their default
        _.each(state, function(value, key) {
            if (config._originalAttributes[key] == value) {
                delete state[key];
            }
        }, this);

        // Merge viewstate with current url parameters and clean it up before shipping
        var params_computed = this.query_parameters(state, uri);

        return params_computed;
    },

    // build an url to self
    // TODO: refactor this elsewhere, e.g. some UrlBuilder?
    make_uri: function(params) {
        var baseurl = navigatorApp.config.get('baseurl');
        var permalink = baseurl + '?' + jQuery.param(this.query_parameters(params));
        return permalink;
    },

    // build an opaque parameter permalink with expiration
    make_uri_opaque: function(params, options) {
        var deferred = $.Deferred();
        var baseurl = this.get_baseurl_patentview();

        // compute opaque parameter variant of permalink parameters
        var params_computed = this.query_parameters(params);
        //log('params_computed:', params_computed);

        opaque_param(params_computed, options).then(function(params_opaque) {
            var permalink = baseurl + '?' + params_opaque;
            deferred.resolve(permalink);
        });

        return deferred.promise();
    },

    // TODO: Refactor to LinkMaker
    get_baseurl_patentview: function() {
        //log('config:', navigatorApp.config);
        var baseurl = navigatorApp.config.get('baseurl');

        // When generating review-in-liveview-with-ttl links on the main patentsearch
        // domain like "patentsearch.example.org" or "navigator.example.org",
        // let's view them on another view-only domain like
        // "patentview.example.org" or "viewer.example.org".
        // Otherwise, fall back to "patentview.ip-tools.io".
        var host = navigatorApp.config.get('request.host');
        if (_.string.contains(host, 'patentsearch')) {
            baseurl = baseurl.replace('patentsearch', 'patentview');
        } else if (_.string.contains(host, 'navigator')) {
            baseurl = baseurl.replace('navigator', 'viewer');
        } else {
            baseurl = baseurl.replace(host, 'patentview.ip-tools.io');
        }

        return baseurl;
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

                // TODO: refactor to separate function

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
                    $(element).popover('toggle');
                });

                // copy permalink to clipboard
                var copy_button = $(tip).find('#permalink-copy');
                navigatorApp.ui.copy_to_clipboard_bind_button('text/plain', uri, {
                    element: copy_button[0],
                    wrapper: this.el,
                    callback: function() { $(element).popover('toggle'); },
                });

                // apply more generic augmentations
                navigatorApp.ui.setup_text_tools();

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
        return require('./permalink.html');
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
        var projectname = navigatorApp.project.get('name');
        // TODO: use in future: var projectname = navigatorApp.config.get('project');

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

    serialize_params: function(params) {

        // Humanized URLs: Serialize specific lists as comma separated items, sorted by value
        var array_whitelist = ['modifiers'];
        _.each(params, function(value, key) {
            if (_.isArray(value) && _.contains(array_whitelist, key)) {
                value = value.sort().join(',');
            }
            params[key] = value;
        });

        // Serialize all items sorted by key
        return jQuery.param(_.sortKeysBy(params));
    },

});


// setup plugin
navigatorApp.addInitializer(function(options) {

    // offer this throughout the whole application
    this.permalink = new PermalinkPlugin();

    this.listenTo(this, 'application:ready', function() {
        this.permalink.setup_ui();
    });

    this.listenTo(this, 'results:ready', function() {
        this.permalink.setup_ui();
    });

});
