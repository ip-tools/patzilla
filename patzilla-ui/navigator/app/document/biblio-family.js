// -*- coding: utf-8 -*-
// (c) 2013-2015 Andreas Motl, Elmyra UG
require('./util.js');

OpsFamilyVerboseMemberView = Backbone.Marionette.ItemView.extend({

    template: require('./biblio-family-verbose-member.html'),
    tagName: 'tr',
    //className: 'row-fluid',
    //style: 'margin-bottom: 10px',

});
_.extend(OpsFamilyVerboseMemberView.prototype, TemplateHelperMixin, TemplateDataContextMixin);


OpsFamilyVerboseCollectionView = Backbone.Marionette.CompositeView.extend({

    template: require('./biblio-family-verbose-collection.html'),
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

    template: require('./biblio-family-compact-member.html'),
    tagName: 'tr',
    //tagName: 'div',
    //className: 'row-fluid',
    //style: 'margin-bottom: 10px',

});
_.extend(OpsFamilyCompactMemberView.prototype, TemplateHelperMixin, TemplateDataContextMixin);


OpsFamilyCompactCollectionView = Backbone.Marionette.CompositeView.extend({

    template: require('./biblio-family-compact-collection.html'),
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
                    // TODO: Review the reference to OpsBaseModel. Could this be refactored somehow?
                    var publication_number = OpsBaseModel.prototype.get_publication_number(item, id_type);
                    members.push(publication_number);
                });

                return members;

            },

        };

    },

});
_.extend(OpsFamilyCompactCollectionView.prototype, TemplateDataContextMixin);


OpsFamilyCitationsMemberView = Backbone.Marionette.ItemView.extend({

    template: require('./biblio-family-citations-member.html'),
    tagName: 'tr',

    templateHelpers: function() {

        var funcs = {};
        // TODO: Review the reference to OpsBaseModel. Could this be refactored somehow?
        funcs = _.extend(funcs, OpsBaseModel.prototype, QueryLinkMixin.prototype);
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
                var citations_environment_button = opsChooserApp.document_details.get_citations_environment_button(exchange_document);
                return citations_environment_button;
            },
        });

        return funcs;

    },

});
_.extend(OpsFamilyCitationsMemberView.prototype, TemplateDataContextMixin);


OpsFamilyCitationsCollectionView = Backbone.Marionette.CompositeView.extend({

    id: "ops-family-citations-collection",
    template: require('./biblio-family-citations-collection.html'),
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
                return opsChooserApp.document_details.get_citations_environment_button(this, options);
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
_.extend(OpsFamilyCitationsCollectionView.prototype, TemplateDataContextMixin);
