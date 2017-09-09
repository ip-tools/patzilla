// -*- coding: utf-8 -*-
// (c) 2013-2015 Andreas Motl, Elmyra UG

OpsBaseViewMixin = {

    bind_query_links: function(container) {

        var _this = this;

        // run search actions when clicking query-links
        container.find(".query-link").unbind('click');
        container.find(".query-link").on('click', function(event) {

            // add important parameters which reflect current gui state (e.g. selected project)
            var href = $(this).attr('href');
            var no_modifiers = $(this).data('no-modifiers');
            var params = opsChooserApp.permalink.query_parameters_viewstate(href, {'no_modifiers': no_modifiers});

            // regardless where the query originates from (e.g. datasource=review),
            // requests for query-links need switching to ops
            params['datasource'] = 'ops';

            // debugging
            //opsChooserApp.config.set('isviewer', true);

            // When in liveview, scrumble database query and viewstate parameters into opaque parameter token
            if (opsChooserApp.config.get('isviewer')) {

                event.preventDefault();
                event.stopPropagation();

                // Nail to liveview mode in any case
                params['mode'] = 'liveview';

                // Compute opaque link parameter and open url
                opsChooserApp.permalink.make_uri_opaque(params).then(function(url) {
                    open(url);
                });


            // Otherwise, serialize state into regular query parameters
            } else {
                $(this).attr('href', '?' + opsChooserApp.permalink.serialize_params(params));
            }

        });

    },


    bind_same_citations_links: function(container) {
        // bind user notification to all same citations links of "explore citation environment" fame
        //container.find('.same-citations-link').unbind('click');
        container.find('.same-citations-link').bind('click', function(event) {
            var citations_length = $(this).data('length');
            if (citations_length > 10) {
                event.preventDefault();
                event.stopPropagation();
                opsChooserApp.ui.notify(
                    'List is capped to the first 10 cited references. Sorry for this limitation.',
                    {type: 'warning', icon: 'icon-cut'});
                var _this = this;
                setTimeout(function() {
                    open($(_this).attr("href"));
                }, 3000);
            }
        });
    },

};

TemplateHelperMixin = {

    templateHelpers: function() {
        var _this = this;
        var funcs = {

            // Propagate configuration object to template
            config: opsChooserApp.config,

            get_linkmaker: function() {
                return new Ipsuite.LinkMaker(_this.model);
            },
        };

        // Propagate whole model object to template
        _.extend(funcs, this.model);

        return funcs;
    },

};

OpsExchangeDocumentView = Backbone.Marionette.Layout.extend({
    //template: "#ops-entry-template",
    template: _.template($('#ops-entry-template').html(), this.model, {variable: 'data'}),
    tagName: 'div',
    className: 'row-fluid',

    regions: {
        region_comment_button: '#region-comment-button',
        region_comment_text: '#region-comment-text',
    },

    initialize: function() {
        console.log('OpsExchangeDocumentView.initialize');
    },

    onDomRefresh: function() {
        console.log('OpsExchangeDocumentView.onDomRefresh');

        // Attach current model reference to result entry dom container so it can be used by different subsystems
        // A reference to the model is required for switching between document details (biblio/fulltext)
        // and for acquiring abstracts from third party data sources.
        // In other words, this is a central gateway between the jQuery DOM world and the Backbone Marionette world.
        // However, there should be better mechanisms. Investigate! (TODO)
        var container = $(this.el).find('.ops-collection-entry');
        $(container).prop('view', this);
        $(container).prop('ops-document', this.model);

        // Swap bibliographic details with placeholder information if we encounter appropriate signal
        // TODO: Really do this onDomRefresh?
        if (this.model.get('__type__') == 'ops-placeholder') {
            //log('this.model:', this.model);

            // Massage LinkMaker to be suitable for use from placeholder template
            this.model.linkmaker = new Ipsuite.LinkMaker(this.model);

            // Add placeholder
            var html = _.template($('#ops-entry-placeholder-template').html(), this.model, {variable: 'model'});
            $(container).find('.ops-bibliographic-details').before(html);

            // Hide content area
            $(container).find('.ops-bibliographic-details').hide();

            // Hide other elements displaying bibliographic data
            $(container).find('.header-biblio,.document-details-chooser').hide();

        }

    },

    signalDrawingLoaded: function() {
        if (this.model.get('__type__') == 'ops-placeholder') {

            // Skip swapping in the first drawing if document has alternative representations on the same result page
            var has_alternatives = !_.isEmpty(this.model.get('alternatives_local'));
            if (has_alternatives) {
                return;
            }

            // Show content area again
            var container = $(this.el).find('.ops-collection-entry');
            $(container).find('.ops-bibliographic-details').show();

            // We don't have any bibliographic data to display, so swap to informational message
            var details = $(container).find('.ops-bibliographic-details').find('.document-details');
            var info = $('<div class="span7"></div>');
            details.replaceWith(info);

            //log('model:', this.model);
            var document_number = this.model.get_document_number();
            var message_not_available =
                'Bummer, OPS does not deliver any bibliographic data for the document "' + document_number + '" ' +
                'and offers no alternative documents to consider.' +
                '<br/><br/>' +
                'However, a drawing was found in one of the upstream patent databases. ' +
                'Please consider checking with the appropriate domestic office by selecting the ' +
                '<a class="btn"><i class="icon-globe icon-large"></i></a> icon in the header bar of this document.' +
                '<br/><br/>' +
                'If the document is not available in any form which satisfies your needs, ' +
                'do not hesitate to report this problem to us!';

            opsChooserApp.ui.user_alert(message_not_available, 'info', info);
        }
    },

    events: {
        'click .rank_up img': 'rankUp',
        'click .rank_down img': 'rankDown',
        'click a.disqualify': 'disqualify',
    },

    render: function() {

        try {
            var args = Array.prototype.slice.apply(arguments);
            var result = Backbone.Marionette.Layout.prototype.render.apply(this, args);
            return result;

        } catch (error) {
            console.error('Error while rendering OpsExchangeDocumentView:', error.message, error.stack);
            var args = Array.prototype.slice.apply(arguments);
            this.model.set('error_message', error.message);
            this.template = '#ops-entry-error-template';
            var result = Backbone.Marionette.Layout.prototype.render.apply(this, args);
            return result;
        }

    },

});

_.extend(OpsExchangeDocumentView.prototype, TemplateHelperMixin);


OpsExchangeDocumentCollectionView = Backbone.Marionette.CompositeView.extend({
    tagName: "div",
    id: "ops-collection-container",
    className: "",
    template: "#ops-collection-template",
    itemView: OpsExchangeDocumentView,

    initialize: function(options) {
        console.log('OpsExchangeDocumentCollectionView.initialize');
    },

    // Override and disable add:render event, see also:
    // https://github.com/marionettejs/backbone.marionette/issues/640
    _initialEvents: function() {
        if (this.collection) {
            //this.listenTo(this.collection, "add", this.addChildView, this);
            this.listenTo(this.collection, "remove", this.removeItemView, this);
            this.listenTo(this.collection, "reset", this.render, this);
        }
    },

    // override the "close" method, otherwise the events bound by "_initialEvents" would vanish
    // which leads to the view children not being re-rendered when resetting its collection.
    // See also region.show(view, {preventClose: true}) in more recent versions of Marionette.
    close: function() {
    },

    onRender: function() {
        console.log('OpsExchangeDocumentCollectionView.onRender');
    },

    onDomRefresh: function() {
        console.log('OpsExchangeDocumentCollectionView.onDomRefresh');
    },

});

MetadataView = Backbone.Marionette.ItemView.extend({
    tagName: "div",
    //id: "paginationview",
    //template: "#ops-metadata-template",
    template: _.template($('#ops-metadata-template').html(), this.model, {variable: 'data'}),

    initialize: function() {
        this.templateHelpers.config = opsChooserApp.config;
        this.listenTo(this.model, "change", this.render);
        this.listenTo(this, "render", this.setup_ui);
    },

    templateHelpers: {},

    setup_ui: function() {
        log('MetadataView.setup_ui');

        $('.content-chooser > button[data-toggle="tab"]').on('show', function (e) {
            // e.target // activated tab
            // e.relatedTarget // previous tab

            var list_type = $(this).data('list-type');
            if (list_type == 'ops') {
                opsChooserApp.listRegion.show(opsChooserApp.collectionView);

            } else if (list_type == 'upstream') {
                opsChooserApp.listRegion.show(opsChooserApp.resultView);
            }

        });

        opsChooserApp.trigger('metadataview:setup_ui');

    },

});


OpsFamilyVerboseMemberView = Backbone.Marionette.ItemView.extend({

    template: _.template($('#ops-family-verbose-member-template').html(), this.model, {variable: 'data'}),
    tagName: 'tr',
    //className: 'row-fluid',
    //style: 'margin-bottom: 10px',

});
_.extend(OpsFamilyVerboseMemberView.prototype, TemplateHelperMixin);


OpsFamilyVerboseCollectionView = Backbone.Marionette.CompositeView.extend({

    template: "#ops-family-verbose-collection-template",
    itemView: OpsFamilyVerboseMemberView,

    id: "ops-family-verbose-verbose-collection",
    //tagName: "div",
    //className: "container-fluid",

    appendHtml: function(collectionView, itemView) {
        collectionView.$('tbody').append(itemView.el);
    }

});
_.extend(OpsFamilyVerboseCollectionView.prototype, TemplateHelperMixin);


OpsFamilyCompactMemberView = Backbone.Marionette.ItemView.extend({

    template: _.template($('#ops-family-compact-member-template').html(), this.model, {variable: 'data'}),
    tagName: 'tr',
    //tagName: 'div',
    //className: 'row-fluid',
    //style: 'margin-bottom: 10px',

});
_.extend(OpsFamilyCompactMemberView.prototype, TemplateHelperMixin);


OpsFamilyCompactCollectionView = Backbone.Marionette.CompositeView.extend({

    //template: "#ops-family-compact-collection-template",
    template: _.template($('#ops-family-compact-collection-template').html(), this.collection, {variable: 'data'}),
    itemView: OpsFamilyCompactMemberView,

    id: "ops-family-compact-collection",
    //tagName: "div",
    //className: "container-fluid",

    appendHtml: function(collectionView, itemView) {
        collectionView.$('tbody').append(itemView.el);
    },

    onDomRefresh: function() {
        this.setup_ui();
    },

    setup_ui: function() {
        OpsBaseViewMixin.bind_query_links(this.$el);
        OpsBaseViewMixin.bind_same_citations_links(this.$el);
    },

    templateHelpers: function() {

        // implement interface required for reusing #ops-citations-environment-button-template
        return {

            // If your template needs access to the collection, you'll need to pass it via templateHelpers
            // https://github.com/marionettejs/backbone.marionette/blob/master/docs/marionette.compositeview.md#composite-model-template
            items: this.collection.toJSON(),

            get_patent_family_member_list: function(id_type) {

                id_type = id_type || 'docdb';

                // aggregate list of publication numbers of all family members
                var members = [];
                _.each(this.items, function(item) {
                    var publication_number = OpsBaseModel.prototype.get_publication_number(item, id_type);
                    members.push(publication_number);
                });

                return members;

            },

        };

    },

});


OpsFamilyCitationsMemberView = Backbone.Marionette.ItemView.extend({

    template: _.template($('#ops-family-citations-member-template').html(), this.model, {variable: 'data'}),
    tagName: 'tr',

    templateHelpers: function() {

        var funcs = {};
        funcs = _.extend(funcs, OpsBaseModel.prototype, OpsHelpers.prototype);
        funcs = _.extend(funcs, {
            get_patent_citation_list: function(enrich) {
                if (this['exchange-document']) {
                    var exchange_document = new OpsExchangeDocument(this['exchange-document']);
                    var citations = exchange_document.get_patent_citation_list(enrich);
                    return citations;
                } else {
                    return [];
                }
            },
            get_citations_environment_button: function() {
                //log('OpsFamilyCitationsMemberView.get_citations_environment_button');
                var exchange_document = new OpsExchangeDocument(this['exchange-document']);
                var citations_environment_button = exchange_document.get_citations_environment_button();
                return citations_environment_button;
            },
        });

        return funcs;

    },

});

OpsFamilyCitationsCollectionView = Backbone.Marionette.CompositeView.extend({

    id: "ops-family-citations-collection",
    //template: "#ops-family-citations-collection-template",
    template: _.template($('#ops-family-citations-collection-template').html(), this.collection, {variable: 'data'}),
    itemView: OpsFamilyCitationsMemberView,

    appendHtml: function(collectionView, itemView) {
        collectionView.$('tbody').append(itemView.el);
    },

    // Override and disable add:render event, see also:
    // https://github.com/marionettejs/backbone.marionette/issues/640
    _initialEvents: function() {
        if (this.collection) {
            //this.listenTo(this.collection, "add", this.addChildView, this);
            this.listenTo(this.collection, "remove", this.removeItemView, this);
            this.listenTo(this.collection, "reset", this.render, this);
        }
    },

    onDomRefresh: function() {
        this.setup_ui();
        this.highlight();
    },

    setup_ui: function() {
        OpsBaseViewMixin.bind_query_links(this.$el);
        OpsBaseViewMixin.bind_same_citations_links(this.$el);
    },

    templateHelpers: function() {

        // Implement interface required for reusing #ops-citations-environment-button-template
        var helpers = {};
        helpers = _.extend(helpers, {

            // If your template needs access to the collection, you'll need to pass it via templateHelpers
            // https://github.com/marionettejs/backbone.marionette/blob/master/docs/marionette.compositeview.md#composite-model-template
            items: this.collection.toJSON(),

            get_citations_environment_button: function(options) {
                //log('OpsFamilyCitationsCollectionView.get_citations_environment_button');
                options = options || {};
                var tpl = _.template($('#ops-citations-environment-button-template').html());
                return tpl({data: this, options: options});
            },

            has_citations: function() {
                return this.items.length > 0;
            },
            get_patent_citation_list: function(links, id_type, options) {

                // FIXME: does not get used yet!
                id_type = id_type || 'docdb';

                options = options || {};

                // aggregate cited references across all family members
                var citations_set = new Set();
                _.each(this.items, function(item) {
                    var exchange_document = new OpsExchangeDocument(item['exchange-document']);

                    // filter US family members
                    if (options.members_no_us) {
                        var office = exchange_document.get('@country');
                        if (office == 'US') {
                            return;
                        }
                    }

                    var citations_local = exchange_document.get_patent_citation_list(false, 'epodoc');
                    _.each(citations_local, function(citation) {
                        citations_set.add(citation);
                    });
                });

                var citations = Array.from(citations_set);
                return citations;

            },

            get_items_query: function(items, fieldname, operator) {
                // FIXME: limit query to 10 items due to ops restriction
                items = items.slice(0, 10);
                items = items.map(function(item) { return fieldname + '=' + item; });
                var query = items.join(' ' + operator + ' ');
                return query;
            },
            get_same_citations_query: function(options) {
                var items = this.get_patent_citation_list(false, 'epodoc', options);
                return this.get_items_query(items, 'ct', 'OR');
            },

            get_citing_query: function() {
                throw Error('not implemented');
            },
            get_publication_number: function(kind) {
                throw Error('not implemented');
            },

        });

        return helpers;

    },

    get_highlight_styles: function() {
        var styles = _.range(0, 360, 35).map(function(hue) {
            var style = {
                backgroundColor: _.template('hsla(  <%= hue %>, 100%, 88%, 1)')({hue: hue}),
            };
            return style;
        });
        return styles;
    },

    highlight: function() {

        // count all cited references
        var citations = {};
        _.each(this.collection.models, function(model) {
            var exchange_document = model.attributes['exchange-document'];
            if (exchange_document && exchange_document['bibliographic-data']) {
                var citation_list = model.get_patent_citation_list(exchange_document['bibliographic-data'], false, 'epodoc');
                _.each(citation_list, function(citation_item) {
                    if (!citations[citation_item]) {
                        citations[citation_item] = 0;
                    }
                    citations[citation_item]++;
                });
            }
        });

        // reject citation references occurring only once
        /*
         // FIXME: use "pick" of more recent underscore release (1.6.0), this can do objects
         citations = _.pick(citations, function(value, key, object) {
         return value > 1;
         });
         */
        _.each(citations, function(value, key) {
            if (value < 2) {
                delete citations[key];
            }
        });


        // highlight citations
        var style_queue;
        var _this = this;
        _.each(citations, function(index, citation) {
            if (!citation) { return; }

            // refill style queue
            if (_.isEmpty(style_queue)) {
                style_queue = _this.get_highlight_styles();
            }

            // get next style available
            var style = style_queue.shift();

            var class_name = _.uniqueId('citation-highlight-');

            // perform highlighting
            _this.$el.highlight(citation, {className: 'highlight-base ' + class_name, wholeWords: true, minLength: 3});

            // apply style
            $('.' + class_name).css(style);

        });

    },

});
