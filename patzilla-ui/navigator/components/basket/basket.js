// -*- coding: utf-8 -*-
// (c) 2013-2017 Andreas Motl, Elmyra UG
require('patzilla.navigator.components.storage');
require('raty');
var memoize = require('memoize');
var urljoin = require('url-join');
var sanitize_non_ascii = require('patzilla.lib.util').sanitize_non_ascii;

function BasketError(message) {
    this.name    = 'BasketError';
    this.message = message;
}

BasketModel = Backbone.RelationalModel.extend({

    sync: Backbone.localforage.sync('Basket'),

    relations: [
        {
            type: Backbone.HasMany,
            key: 'entries',
            relatedModel: 'BasketEntryModel',
            includeInJSON: Backbone.Model.prototype.idAttribute,

            // reverseRelation *must not* be defined for HasMany relationships, otherwise this will yield
            // empty collections unconditionally, especially after creating new parent objects
            /*
            reverseRelation: {
                type: Backbone.One,
                key: 'basket',
                // 'relatedModel' is automatically set to 'ProjectModel'
                includeInJSON: Backbone.Model.prototype.idAttribute,
            },
            */

        }
    ],

    defaults: {
    },

    initialize: function() {
        console.log('BasketModel.initialize', this);

        // backbone-relational backward-compat
        if (!this.fetchRelated) this.fetchRelated = this.getAsync;

        // memoize results of "get_numbers"
        this.wrap_cache('get_numbers');

    },

    // memoize results of method, invalidating cache on model change
    wrap_cache: function(funcname, context) {
        context = context || this;

        // cache return value of function
        this[funcname] = memoize(this[funcname], this);

        // method for invalidating the cache
        this.invalidate_cache = function() {
            //this[funcname].__cache.remove();
            this[funcname].__cache.purge();
        };

        // invalidate cache on all model change events
        //this.on('change', this.invalidate_cache);
        this.on('change:add', this.invalidate_cache);
        this.on('change:remove', this.invalidate_cache);
        this.on('change:rate', this.invalidate_cache);
    },

    // initialize model from url query parameters ("numberlist")
    init_from_query: function() {

        var _this = this;

        var numberlist = navigatorApp.config.get('numberlist');
        var context = navigatorApp.config.get('context');

        // Debugging
        //log('numberlist:', numberlist);
        //log('context:', context);

        var deferred = $.Deferred();

        if (numberlist) {

            numberlist = decodeURIComponent(numberlist);
            var entries = numberlist.split(/[,\n]/);

            if (context == 'viewer') {

                _this.save({'entries': []}, {
                    success: function() {
                        var deferreds = [];
                        $.when(_this.fetch_entries()).then(function() {
                            _(entries).each(function(entry) {
                                //log('entry:', entry);
                                var deferred = _this.add(entry);
                                deferreds.push(deferred);
                            });
                            deferreds.push(_this.fetch_entries());
                        });
                        // Wait for all "add" operations to finish before signalling success
                        $.when(deferreds_bundle(deferreds)).then(function() {
                            deferred.resolve();
                        })
                    },
                    error: function() {
                        console.error('Error creating basket from query parameters');
                        deferred.resolve();
                    },
                });

            } else {
                deferred.resolve();
            }

        } else {
            deferred.resolve();
        }

        return deferred.promise();
    },

    get_entry_by_number: function(item) {

        // Fix exception flood occurred on 2017-03-29
        var entries = this.get('entries');
        if (!entries) {
            return;
        }

        var entrymodels = entries.where({number: item});
        if (_.isEmpty(entrymodels)) {
            return;
        } else {
            return entrymodels[0];
        }
    },

    exists: function(number) {
        var item = this.get_entry_by_number(number);
        return item ? true : false;
    },

    // add item to basket
    add: function(number, options) {

        options = options || {};

        var _this = this;

        if (_.isEmpty(number)) return;
        number = number.trim();
        if (_.isEmpty(number)) return;

        var deferred = $.Deferred();

        var entry = this.get_entry_by_number(number);
        if (entry) {

            function _refetch() {
                // refetch entry to work around localforage.backbone vs. backbone-relational woes
                // otherwise, data storage mayhem may happen, because of model.id vs. model.sync.localforageKey mismatch
                entry.fetch({success: function() {

                    // 2015-12-22: remove "title" attributes from BasketEntry objects
                    delete entry['title'];

                    deferred.resolve(entry);

                    // refresh gui, update timestamp
                    // 2016-08-03: Remove it, because it interacts badly with some button event registrations. Let's see how it goes....
                    // 2016-08-04: Maybe it's important for getting the "Fade seen documents" feature right...
                    //             Answer: Yes, it's very important for keeping the visual
                    //             representation of basket contents in sync with the model.
                    !options.bulk && _this.trigger('change', _this);
                }});
            }

            if (options.reset_seen) {
                entry.save({'seen': false}, {success: function() {
                    _refetch();
                }});
            } else {
                _refetch();
            }

            return deferred.promise();
        }

        // Get title of selected document
        // 2015-12-22: Stop storing "title" attributes.
        //             Deactivated due to default database size constraints (5 MB)
        //             our first user seems to have hit this limit!
        /*
        // TODO: maybe prebuild/maintain an index in collection
        var document = _.find(navigatorApp.documents.models, function(doc) {
            var document_number = doc.get_document_number();
            return number == document_number;
        });
        var title = document ? document.attributes.get_title_list() : undefined;
        */

        // build basket entry
        entry = new BasketEntryModel({
            number: number,
            timestamp: now_iso(),

            // 2015-12-22: stop storing "title" attributes
            //title: title,

            /*basket: this,*/
            /*query: null,*/
        });

        if (options.reset_seen) {
            entry.save({'seen': false});
        }

        // save basket entry
        entry.save(null, {success: function() {
            var entries = _this.get('entries');
            entries.add(entry);
            _this.save({'entries': entries}, {
                success: function() {
                    if (options.bulk) {
                        deferred.resolve(entry);
                    } else {
                        $.when(_this.fetch_entries()).then(function() {
                            //deferred.resolve(entry);
                            deferred.resolve(_this.get_entry_by_number(entry.get('number')));
                            _this.trigger('change', _this);
                            _this.trigger('change:add', entry, number);
                        });
                    }
                },
            });
        }});

        return deferred.promise();
    },

    add_multi: function(numberlist, options) {

        options = options || {};
        _(options).extend({bulk: true});

        var deferred = $.Deferred();

        var _this = this;
        var deferreds = [];
        _.each(numberlist, function(number) {
            deferreds.push(_this.add(number, options));
        });
        $.when.apply($, deferreds).then(function() {
            _this.refresh();
            deferred.resolve();
        });

        return deferred.promise();
    },

    refresh: function() {
        var _this = this;
        $.when(this.fetch_entries()).then(function() {
            _this.trigger('change');
        });
    },

    // remove item from basket
    remove: function(number) {
        var _this = this;

        var entry = this.get_entry_by_number(number);
        if (!entry) {
            return;
        }

        var entries = this.get('entries');
        entries.remove(entry);
        entry.destroy();
        _this.save({'entries': entries}, {success: function() {
            $.when(_this.fetch_entries()).then(function() {
                _this.trigger('change:remove', entry, number);
                _this.trigger('change', _this);
            });
        }});
    },

    get_entries: function(options) {
        options = options || {};

        var entries = this.get('entries').models;
        //log('entries:', entries);

        entries = _(entries).reject(function(entry) {

            // let all entries pass
            //return false;

            if (entry.get('number') == undefined) {
                return true;
            }

            var score = entry.get('score');
            var seen = entry.get('seen');
            var dismiss = entry.get('dismiss');

            var outcome = false;
            if (options.dismiss != undefined) {
                if (options.dismiss == false && (dismiss == undefined || dismiss == false)) {
                    outcome = false;
                } else if (options.dismiss == true && dismiss == true) {
                    return false;
                } else {
                    return true;
                }
            }
            if (options.seen != undefined) {

                var outcome;
                if (options.seen == false && (seen == undefined || seen == false)) {
                    outcome |= false;
                } else if (seen == undefined) {
                    outcome |= options.seen;
                } else {
                    outcome |= seen == !options.seen;
                }

                // Debugging
                /*
                if (entry.get('number') == 'DE7914954U1') {
                    log('options:', options);
                    log('entry:', entry);
                    log('outcome:', outcome);
                }
                */

                return outcome;
            }
            return false;
        });

        return entries;

    },

    get_numbers: function(options) {
        options = options || {};

        if (options.honor_dismiss) {
            options.dismiss = false;
        }
        _(options).defaults({seen: false});
        //log('options:', options);

        var entries = this.get_entries(options);

        var numbers = entries.map(function(entry) {
            return sanitize_non_ascii(entry.get('number'));
        });
        //log('numbers:', numbers);

        return numbers;
    },

    empty: function(options) {
        var entries = this.get_entries(options);
        return entries.length == 0;
    },

    csv_list: function() {
        var entries = this.get_entries({'seen': false});
        return entries.map(function(entry) {
            var parts = [
                entry.get('number'),
                entry.get('score'),
                entry.get('dismiss')
            ];
            var line = parts.join(',');
            return line;
        });
    },

    get_records: function(options) {
        var entries = this.get_entries(options);
        var baseurl = navigatorApp.permalink.get_baseurl_patentview();
        return entries.map(function(entry) {
            var newentry = entry.toJSON();
            if (!newentry) { return; }
            newentry['number'] = sanitize_non_ascii(newentry['number']);
            newentry['url'] = urljoin(baseurl, '/view/pn/', newentry['number']);
            return newentry;
        });
    },

    unicode_stars_list: function() {
        var entries = this.get_entries({'seen': false});
        return entries.map(function(entry) {
            var line =
                    _.string.ljust(entry.get('number'), 20, ' ') +
                        _.string.ljust(entry.get('dismiss') ? '∅' : '', 5, ' ') +
                        (entry.get('seen') ? 'seen' : '') +
                        _.string.repeat('★', entry.get('score'));
            return line;
        });
    },

    unicode_stars_list_email: function() {
        var nbsp = String.fromCharCode(160);
        var entries = this.get_entries({'seen': false});
        return entries.map(function(entry) {
            var dismiss_and_score = (entry.get('dismiss') ? '∅' : '') + _.string.repeat('★', entry.get('score'));
            var padlen = 10 - dismiss_and_score.length * 1.7;
            var padding = _.string.repeat(nbsp, padlen);
            var line = dismiss_and_score + padding + entry.get('number');
            return line;
        });
    },

    review: function(options) {

        var publication_numbers = this.get_numbers();
        //var publication_numbers = this.get_numbers({seen: true});
        //var publication_numbers = this.get_numbers({honor_dismiss: true});
        //log('publication_numbers:', publication_numbers);

        var hits = publication_numbers.length;

        // TODO: decouple from referencing the main application object e.g. by using events!?
        navigatorApp.set_datasource('review');
        navigatorApp.metadata.set('reviewmode', true);
        navigatorApp.populate_metadata();
        navigatorApp.perform_listsearch(options, undefined, publication_numbers, hits, 'pn', 'OR');
    },

    // fetch all basket entries from datastore, one by one; this is nasty
    fetch_entries: function() {

        var _this = this;
        var main_deferred = $.Deferred();
        $.when(this.fetchRelated('entries')).then(function() {

            // TODO: refactor this to some common base class or mixin
            var deferreds = [];
            _this.get('entries').each(function(entry) {

                // prepare a deferred which will get resolved after successfully fetching an item from datastore
                var deferred = $.Deferred();
                deferreds.push(deferred.promise());

                entry.fetch({
                    success: function() {
                        deferred.resolve(entry);
                    },
                    error: function(e) {
                        // HACK: sometimes, the item has vanished while fetching from store, so let's recreate it
                        console.warn('Error while fetching basket entry:', e, entry);
                        entry.save(null, {
                            success: function() {
                                console.log('Success when re-saving basket entry');
                                deferred.resolve(entry);
                            },
                            error: function() {
                                console.warn('Error when re-saving basket entry');
                                deferred.resolve(entry);
                            },
                        });
                    }
                });
            });

            $.when.apply($, deferreds).then(function() {
                main_deferred.resolve();
            });
        });

        return main_deferred.promise();

    },

    get_view_state: function(more) {

        more = more || {};

        var projectname = navigatorApp.project.get('name');
        var numbers = this.get_numbers();
        var numbers_string = numbers.join(',');

        var state = {
            //mode: 'liveview',
            context: 'viewer',
            project: projectname,
            query: undefined,
            //datasource: 'review',
            numberlist: numbers_string,
        };

        _(state).extend(more);

        return state;

    },

    share_email_params: function() {

        var projectname = navigatorApp.project.get('name');
        var url = navigatorApp.permalink.make_uri(this.get_view_state({project: 'via-email'}));

        var numbers = this.get_numbers();
        var numbers_count = numbers.length;

        var basket_csv = this.csv_list();
        var basket_stars = this.unicode_stars_list_email();

        var subject = _.template('Shared <%= count %> patent numbers through project "<%= projectname %>" at <%= date %>')({
            count: numbers_count,
            date: now_iso_human(),
            projectname: projectname,
        });

        var body_tpl = _.template($('#basket-mail-template').html().trim());
        var body = body_tpl({
            subject: subject,
            basket_plain: numbers.join('\n'),
            basket_csv: basket_csv.join('\n'),
            basket_stars: basket_stars.join('\n'),
            url: url,
        });

        var data = {
            subject: '[IPSUITE] ' + subject,
            body: body,
        };

        return data;
    },

    get_numberlist_url: function() {
        if (this.empty()) {
            return;
        }
        var url = navigatorApp.permalink.make_uri(this.get_view_state());
        return url;
    },

    get_numberlist_url_liveview: function(ttl) {
        if (this.empty()) {
            return;
        }
        return navigatorApp.permalink.make_uri_opaque(this.get_view_state({mode: 'liveview', datasource: 'review'}), {ttl: ttl});
    },

});


BasketEntryModel = Backbone.RelationalModel.extend({

    sync: Backbone.localforage.sync('BasketEntry'),

    defaults: {
        number: undefined,
        timestamp: undefined,
        // 2015-12-22: stop storing "title" attributes
        //title: undefined,
        score: undefined,
        dismiss: undefined,
        seen: undefined,
        // TODO: link to QueryModel
        //query: undefined,
    },

    initialize: function() {
        //console.log('BasketEntryModel.initialize');
    },
});

Backbone.Relational.store.addModelScope({BasketModel: BasketModel, BasketEntryModel: BasketEntryModel});


BasketView = Backbone.Marionette.ItemView.extend({

    template: require('./basket.html'),

    initialize: function() {
        //console.log('BasketView.initialize');
        this.listenTo(this.model, "change", this.render);
        this.listenTo(this, "item:rendered", this.setup_ui);
        this.templateHelpers.config = navigatorApp.config;
    },

    templateHelpers: {},

    serializeData: function() {

        var data = {};
        data = this.model.toJSON();

        var entries = this.model.unicode_stars_list();

        if (entries) {
            data['numbers_display'] = entries.join('\n');
        }

        return data;

    },

    setup_ui: function() {
        console.log('BasketView.setup_ui');

        var _this = this;

        // display number of entries in basket

        var entry_count = this.model.get_entries({'seen': false}).length;
        $('.basket-entry-count').text(entry_count);

        var seen_count = this.model.get_entries({'seen': true}).length;
        $('.basket-seen-count').text(seen_count);


        // only enable submit button, if ship url is given
        var ship_url = navigatorApp.config.get('ship-url');
        if (ship_url) {
            $('#basket-submit-button').removeClass('hide');
        } else {
            $('#basket-submit-button').addClass('hide');
        }

        // import clipboard content by intercepting paste event
        $("#basket").off('paste').on('paste', function(e) {
            e.preventDefault();
            var text = (e.originalEvent || e).clipboardData.getData('text');
            var entries = text.split(/[,;\r\n]/);
            _.each(entries, function(entry) {
                entry = sanitize_non_ascii(entry);
                if (entry) {
                    _this.model.add(entry);
                }
            });
        });

        // basket import
        $('#basket-import-button').off('click').on('click', function(e) {
            _this.future_premium_feature();
            return false;
        });

        // review feature: trigger search from basket content
        $('#basket-review-button').off('click').on('click', function(event) {
            event.preventDefault();
            if (_this.check_empty({kind: 'review', icon: 'icon-indent-left', seen: false})) { return; }

            // Start review mode
            navigatorApp.metadata.resetSomeDefaults(['pagination_current_page', 'page_size']);
            _this.model.review();
        });
        // disable counter buttons, required to retain popover
        $('#basket-entry-count-button,#basket-seen-count-button').off('click').on('click', function(event) {
            event.preventDefault();
            event.stopPropagation();
        });

        // submit selected documents to origin or 3rd-party system
        $('#basket-submit-button').off('click').on('click', function() {
            if (_this.check_empty()) { return; }
            var numbers = _this.model.get_numbers();
            $('textarea#basket').val(numbers.join('\n'));
        });


        // Export Dossier
        $('#dossier-export-button').off('click').on('click', function(event) {

            if (!navigatorApp.component_enabled('export')) {
                var message = 'Export feature not enabled.';
                console.warn(message);
                navigatorApp.ui.notify(message, {type: 'warning', icon: 'icon-save'});
                return;
            }

            // Don't export empty baskets
            if (_this.check_empty({kind: 'export'})) {
                return;
            }

            // Open shiny export dialog
            navigatorApp.exporter.open_dialog({
                element: this,
                event: event,
            });

        });

        this.$el.find('.btn-popover').popover();


        /*

        // wire display-results buttons
        $('#share-display-rated').off('click');
        $('#share-display-rated').on('click', function(e) {
            var modal = new ModalRegion({el: '#modal-area'});
            var basket_list_view = new BasketListView({});
            modal.show(basket_list_view);
        });
        $('#share-display-seen').off('click');
        $('#share-display-seen').on('click', function(e) {
            var modal = new ModalRegion({el: '#modal-area'});
            var basket_list_view = new BasketListView({'seen': true});
            modal.show(basket_list_view);
        });

        // share via mail
        $('#share-numberlist-email').off('click');
        $('#share-numberlist-email').on('click', function() {
            if (_this.check_empty()) { return; }
            var params = _this.model.share_email_params();
            var mailto_link = 'mailto:?' + jQuery.param(params).replace(/\+/g, '%20');
            //log('mailto_link:', mailto_link);
            $(this).attr('href', mailto_link);
        });

        // share via clipboard
         navigatorApp.ui.copy_to_clipboard('text/plain', function() {
            if (_this.check_empty()) { return; }
            var numbers = _this.model.get_numbers();
            return numbers.join('\n');
        }, {element: $('#share-numberlist-clipboard')});

        // share via url
        $('#share-numberlist-url').off('click');
        $('#share-numberlist-url').on('click', function() {
            if (_this.check_empty()) { return; }
            var url = navigatorApp.permalink.make_uri(_this.model.get_view_state());
            $(this).attr('target', '_blank');
            $(this).attr('href', url);
        });

        // share via url, with ttl
        $('#share-numberlist-url-ttl').off('click');
        $('#share-numberlist-url-ttl').on('click', function(e) {

            e.preventDefault();
            e.stopPropagation();

            if (_this.check_empty()) { return; }

            var anchor = this;
            navigatorApp.permalink.make_uri_opaque(_this.model.get_view_state({mode: 'liveview'})).then(function(url) {

                // v1: open url
                //$(anchor).attr('href', url);

                // v2: open permalink popover

                navigatorApp.permalink.popover_show(anchor, url, {
                    title: 'External document review',
                    intro:
                        '<small>' +
                            'This offers a link for external/anonymous users to review the collected documents. ' +
                            'It will just transfer the plain numberlist without any rating scores.' +
                        '</small>',
                    ttl: true,
                });

            });
        });

        // download zip archive of pdf documents
        $('#download-documents-pdf-archive').off('click');
        $('#download-documents-pdf-archive').on('click', function() {
            if (_this.check_empty()) { return; }
            var numberlist = navigatorApp.basketModel.get_numbers();
            //log('numberlist:', numberlist);
            $(this).attr('target', '_blank');
            $(this).attr('href', '/api/pdf/' + numberlist.join(','));
        });

        */

        // share via document transfer
        $('#share-documents-transfer').off('click');
        $('#share-documents-transfer').on('click', function() {
            _this.future_premium_feature();
        });


        // simple permalink
        $('.permalink-review-liveview').off('click');
        $('.permalink-review-liveview').on('click', function(e) {

            e.preventDefault();
            e.stopPropagation();

            // generate permalink uri and toggle popover
            var _button = this;
            navigatorApp.permalink.liveview_with_database_params().then(function(params) {

                // compute permalink
                var url = navigatorApp.permalink.make_uri(params);

                // show permalink overlay
                navigatorApp.permalink.popover_show(_button, url, {
                    intro:
                        '<small>' +
                            'This offers a persistent link to review the current project. ' +
                            'It will transfer the whole project structure including queries and basket content with rating scores.' +
                            '</small>',
                });

            });
        });

        // signed permalink with time-to-live
        $('.permalink-review-liveview-ttl').off('click');
        $('.permalink-review-liveview-ttl').on('click', function(e) {

            e.preventDefault();
            e.stopPropagation();

            // generate permalink uri and toggle popover
            var _button = this;
            navigatorApp.permalink.liveview_with_database_params().then(function(params) {

                // compute permalink
                navigatorApp.permalink.make_uri_opaque(params).then(function(url) {

                    // show permalink overlay
                    navigatorApp.permalink.popover_show(_button, url, {
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

    check_empty: function(options) {
        options = options || {};
        var verb = 'shared';
        if (options.kind == 'review') {
            verb = 'reviewed';
        } else if (options.kind == 'export') {
            verb = 'exported';
        }
        if (!options.icon) {
            options.icon = 'icon-external-link';
        }
        if (this.model.empty(options)) {
            navigatorApp.ui.notify(
                "An empty collection can't be " + verb + ", please add some documents.",
                {type: 'warning', icon: options.icon + ' icon-large'});
            return true;
        }
        return false;
    },

    future_premium_feature: function() {
        bootbox.dialog(
            'Available soon via subscription.', [{
                "label": 'OK',
                "icon" : 'OK',
                "callback": null,
            }],
            {header: 'Future feature'});
    },

    textarea_scroll_bottom: function() {
        $('#basket').scrollTop($('#basket')[0].scrollHeight);
    },

    textarea_scroll_text: function(text) {
        var textArea = $('#basket');
        var index = textArea.text().search(text);
        if (index) {
            textArea.scrollTop(index);
        }
    },

});

BasketController = Marionette.Controller.extend({

    initialize: function(options) {
        console.log('BasketController.initialize');
    },

    // backpropagate current basket entries into action state (rating, signal coloring, etc.)
    link_document: function(entry, number) {

        //log('link_document', entry, number);

        // Update basket view
        navigatorApp.basketView.render();

        // why do we have to access the global object here?
        // maybe because of the event machinery which dispatches to us?
        var numbers = navigatorApp.basketModel ? navigatorApp.basketModel.get_numbers() : [];
        //log('link_document numbers:', numbers);

        var checkbox_element = $('#chk-patent-number-' + number);
        var add_button_element = $('#add-patent-number-' + number);
        var remove_button_element = $('#remove-patent-number-' + number);
        var rating_widget = $('#rate-patent-number-' + number);
        var indicator_element = rating_widget.closest('.ops-collection-entry-heading');

        // number is not in basket, show "add" button
        if (!_(numbers).contains(number)) {
            checkbox_element && checkbox_element.prop('checked', false);
            add_button_element && add_button_element.show();
            remove_button_element && remove_button_element.hide();

            // clear rating widget
            rating_widget.raty('reload');

            // clear color indicators
            indicator_element.toggleClass('dismiss', false);
            indicator_element.toggleClass('score1', false);
            indicator_element.toggleClass('score2', false);
            indicator_element.toggleClass('score3', false);

        // number is already in basket, show "remove" button and propagate rating values
        } else {
            checkbox_element && checkbox_element.prop('checked', true);
            add_button_element && add_button_element.hide();
            remove_button_element && remove_button_element.show();

            // if we have a model, propagate "score" and "dismiss" values
            if (entry) {
                var score = entry.get('score');
                var dismiss = entry.get('dismiss');

                // a) to rating widget
                rating_widget.raty('score', score);
                rating_widget.raty('dismiss', dismiss);

                // b) to color indicator
                indicator_element.toggleClass('dismiss', Boolean(dismiss));
                indicator_element.toggleClass('score1', score == 1);
                indicator_element.toggleClass('score2', score == 2);
                indicator_element.toggleClass('score3', score == 3);

            }

        }

        // properly handle "seen" state
        // display document with full opacity if not marked as "seen"
        if (entry) {
            if (!entry.get('seen')) {
                navigatorApp.document_base.bright(rating_widget);
            }
        }

    },

});


BasketListView = GenericResultView.extend({

    initialize: function(options) {
        console.log('BasketListView.initialize');
        this.options = options;
        this.message_more = '';
    },

    setup_data: function(data) {

        var numberlist = data;

        var numberlist_string = numberlist.join('\n');

        // transfer to textarea
        $('#result-content').val(numberlist_string);

        this.setup_numberlist_buttons(numberlist);
        this.hide_button_to_basket();

    },

    start: function() {

        this.indicate_activity(true);
        this.user_message('Computing results, please stand by. &nbsp; <i class="spinner icon-refresh icon-spin"></i>', 'info');

        var response = navigatorApp.basketModel.get_numbers(this.options);

        // transfer data
        this.setup_data(response);

        // notify user
        this.indicate_activity(false);
        var length = NaN;
        if (_.isArray(response)) {
            length = response.length;
        }
        if (_.isObject(response)) {
            length = Object.keys(response).length;
        }
        var message = length + ' collection item(s).';
        if (this.message_more) {
            message += this.message_more;
        }
        this.user_message(message, 'success');

    },

});


RatingController = Marionette.Controller.extend({

    initialize: function(options) {
        console.log('RatingController.initialize');
    },

    setup_ui: function(options) {

        console.log('Setup rating widget');
        //$('.rating-widget').raty('destroy');
        $('.rating-widget').raty({
            number: 3,
            hints: ['slightly relevant', 'relevant', 'important'],
            cancel: true,
            cancelHint: 'not relevant',
            dismissible: true,
            action: function(data, evt) {
                var score = data.score;
                var dismiss = data.dismiss;
                var document_number = $(this).data('document-number');
                options.callback(document_number, score, dismiss);
            },
        });

    },


});

// setup component
navigatorApp.addInitializer(function(options) {

    this.basketController = new BasketController();
    this.rating = new RatingController();

    // Special bootstrap handling for datasource=review:
    // This activates the review after both the application
    // and the basket signal readyness.
    this.listenTo(this, 'application:ready', function() {
        if (this.config.get('datasource') == 'review') {
            this.listenToOnce(this, 'basket:activated', function(basket) {
                $.when(basket.init_from_query()).then(function() {
                    basket.review();
                });
            });
        }
    });

    this.register_component('basket');

});
