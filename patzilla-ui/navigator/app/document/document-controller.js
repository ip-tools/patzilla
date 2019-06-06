// -*- coding: utf-8 -*-
// (c) 2014-2018 Andreas Motl <andreas.motl@ip-tools.org>
require('jquery.shorten.1.0');
require('./util.js');
var Nataraja = require('patzilla.navigator.components.nataraja').Nataraja;


DocumentBaseController = Marionette.Controller.extend({

    initialize: function(options) {
        console.log('DocumentBaseController.initialize');
    },

    setup_ui: function() {

        // ------------------------------------------
        //   element visibility
        // ------------------------------------------
        navigatorApp.ui.do_element_visibility();


        // ------------------------------------------
        //   print mode
        // ------------------------------------------
        var MODE_PRINT = navigatorApp.config.get('mode') == 'print';
        if (MODE_PRINT) {
            return;
        }


        // ------------------------------------------
        //   metadata area
        // ------------------------------------------

        // shorten cql query string
        $(".cql-query").shorten({showChars: 125, moreText: 'more', lessText: 'less'});


        // ------------------------------------------
        //   second pagination at bottom
        // ------------------------------------------
        //$(navigatorApp.paginationViewBottom.el).show();


        // ------------------------------------------
        //   result list
        // ------------------------------------------
        navigatorApp.basket_bind_actions();

        // use jquery.shorten on "abstract" text
        $(".abstract").shorten({showChars: 2000, moreText: 'more', lessText: 'less'});

        // popovers
        // TODO: rename to just "popover" or similar, since not just buttons may have popovers
        $('.btn-popover').popover();

        // tooltips
        // TODO: rename to just "tooltip" or similar, since tooltipping is universal
        $('.inid-tooltip').tooltip();


        // lazy german abstract acquisition
        $('.abstract-acquire').on('click', function(event) {
            event.preventDefault();
            var lang = $(this).data('lang');

            var document = navigatorApp.document_base.get_document_by_element(this);

            $(this).after('<span class="abstract-acquire-spinner">&nbsp;&nbsp;<i class="icon-refresh icon-spin"></i></span>');

            var ft = navigatorApp.document_details.get_fulltext(document);
            var _this = this;
            ft.get_abstract(lang).then(function(data) {
                    $(_this).replaceWith(data['html']);
                    $('.abstract-acquire-spinner').detach();

                }).fail(function(data) {
                    $(_this).replaceWith(data['html']);
                    $('.abstract-acquire-spinner').detach();
            });
        });


        // ------------------------------------------
        //   embed per-item 3rd-party component
        // ------------------------------------------
        $('.embed-item').each(function(idx, embed_container) {
            var embed_item_url = $(embed_container).data('embed-url');
            var document_number = $(embed_container).data('document-number');
            if (embed_item_url) {

                // 1. compute url to component
                var _tpl = _.template(embed_item_url, { interpolate: /\{\{(.+?)\}\}/g });
                var embed_real_url = _tpl({publication_number: document_number});

                // 2. create an iframe
                var iframe = '<iframe src="' + embed_real_url + '" class="container-fluid well" seamless="seamless" height2="200" width2="100%" style="min-height: 50%; min-width: 80%"/>';
                $(this).append(iframe);

            }
        });


        // ------------------------------------------
        //   "family citations" module
        // ------------------------------------------
        var module_name = 'family-citations';
        var module_available = navigatorApp.user_has_module(module_name);

        // Shortcut button for jumping to Family » Citations
        $('.family-citations-shortcut-button').off('click');
        $('.family-citations-shortcut-button').on('click', function(event) {
            if (module_available) {
                var container = $(this).closest('.ops-collection-entry');
                container.find('.document-details-chooser > button[data-toggle="tab"][data-details-type="family"]').tab('show');
                container.find('.family-chooser > button[data-toggle="tab"][data-view-type="citations"]').tab('show');
            } else {
                navigatorApp.ui.notify_module_locked(module_name);
            }
        });


        // Apply stuff to all document panels
        var entry_elements = $('.ops-collection-entry');

        // Override clicking on any inline links to propagate important
        // view state parameters by amending the url on the fly
        OpsBaseViewMixin.bind_query_links(entry_elements);

        // Override clicking of "citation explore » documents with same citations" button
        // for introducing warning message when having len(citations) > 10
        OpsBaseViewMixin.bind_same_citations_links(entry_elements);

    },

    get_collection_entry_by_element: function(element) {
        return $(element).closest('.ops-collection-entry');
    },

    get_document_by_element: function(element) {
        return this.get_collection_entry_by_element(element).prop('ops-document');
    },

    dim: function(element) {
        var entry = this.get_collection_entry_by_element(element);
        entry.fadeTo('slow', 0.33);
    },

    bright: function(element) {
        var entry = this.get_collection_entry_by_element(element);
        entry.fadeTo('slow', 1);
    },

});


DocumentDetailsController = Marionette.Controller.extend({

    initialize: function(options) {
        log('DocumentDetailsController.initialize');
        this.nataraja = new Nataraja();
    },

    setup_ui: function() {

        log('DocumentDetailsController.setup_ui');

        var _this = this;

        // --------------------------------------------
        //   toggle detail view (description, claims)
        // --------------------------------------------
        // TODO: refactor to ops.js
        $('.document-details-chooser > button[data-toggle="tab"]').on('show', function (e) {

            //log('ONSHOW ONSHOW: .document-details-chooser');

            // e.target // activated tab
            // e.relatedTarget // previous tab

            var container = $($(e.target).attr('href'));
            var details_type = $(this).data('details-type');
            var details_title = $(this).data('details-title');

            var document = navigatorApp.document_base.get_document_by_element(this);

            if (document) {

                // Setup fulltext display.
                if (_(['claims', 'description']).contains(details_type)) {

                    // Acquire fulltext information and display it.
                    var details = _this.get_fulltext_details(details_type, document);
                    _this.display_fulltext(details, {element: container, type: details_type, title: details_title});

                // Setup family information display.
                } else if (details_type == 'family') {

                    // Setup more button event handlers.
                    var family_chooser = $(container).find('.family-chooser');
                    family_chooser.find('button[data-toggle="tab"]').on('show', function (e) {
                        var view_type = $(this).data('view-type');
                        if (view_type == 'citations') {
                            var module_name = 'family-citations';
                            var module_available = navigatorApp.user_has_module(module_name);
                            if (module_available) {
                                _this.display_family(document, container, view_type);
                            } else {
                                navigatorApp.ui.notify_module_locked(module_name);
                            }

                        } else {
                            _this.display_family(document, container, view_type);
                        }
                    });

                    // Initial configuration.
                    var active_tab = family_chooser.find('button[data-toggle="tab"][class*="active"]');
                    var view_type = $(active_tab).data('view-type');
                    _this.display_family(document, container, view_type);

                }
            }

            // fix missing popover after switching inline detail view
            $('.btn-popover').popover();
        });

    },

    get_fulltext: function(document) {

        // Resolve effective fulltext datasource by country in order of definition
        var datasource_name;
        var country = document.get('@country');
        _.find(navigatorApp.config.get('system').datasources, function(name) {
            var datasource_info = navigatorApp.config.get('system').datasource[name];
            if (_.contains(datasource_info.fulltext_countries, country)) {
                datasource_name = name;
                return true;
            }
        });

        // Resolve handler and appropriate document number representation
        // TODO: Refactor to patzilla.access.{epo-ops,depatisconnect,ificlaims} namespaces
        var clazz;
        var document_number;
        if (datasource_name == 'ops') {
            clazz = OpsFulltext;
            document_number = document.get_publication_number('docdb');
            log('Acquiring fulltext information for ' + document_number);

        } else if (datasource_name == 'depatisconnect') {
            clazz = DepatisConnectFulltext;
            document_number = document.get_publication_number('docdb');

        } else if (datasource_name == 'ificlaims') {
            clazz = IFIClaimsFulltext;
            document_number = document.get_publication_number('docdb');

        } else {
            navigatorApp.ui.notify(
                'Fulltext of document from country "' + country + '" not available. No appropriate datasource configured.',
                {type: 'warning', icon: 'icon-file-text-alt'});
            return;

        }

        return new clazz(document_number);
    },

    get_fulltext_details: function(details_type, document) {
        var ft = this.get_fulltext(document);
        if (!ft) {
            var deferred = $.Deferred();
            deferred.reject({html: 'No data available'});
            return deferred.promise();
        }
        if (details_type == 'description') {
            return ft.get_description();
        } else if (details_type == 'claims') {
            return ft.get_claims();
        }
    },

    display_fulltext: function(details, options) {
        var _this = this;

        var container = options.element;
        var title = options.title;

        var content_element = container.find('*[data-area="fulltext"]');

        var identifier = container.data('identifier');

        //var template_single = _.template($('#document-fulltext-template').html(), {variable: 'data'});
        var template_single = require('./fulltext.html');

        if (content_element) {
            this.indicate_activity(container, true);
            details.then(function(data, datasource_label) {
                _this.indicate_activity(container, false);
                if (data) {

                    // Legacy format: Object w/o language, just contains "html" and "lang" attributes.
                    if (data.html) {
                        var content = template_single({
                            type: options.type,
                            title: title,
                            language: data.lang,
                            content: data.html,
                            datasource: datasource_label,
                        });
                        content_element.html(content);

                    // New format: Object keyed by language.
                    } else {

                        // Todo: Make this list configurable by user preferences.
                        var language_sort_order = ['EN', 'DE', 'FR'];

                        var language_sort_criteria = function(value) {
                            var index = language_sort_order.indexOf(value);
                            if (index == -1) {
                                return 999;
                            } else {
                                return index;
                            }
                        };

                        var languages = _(data).keys();
                        languages = _.sortBy(languages, language_sort_criteria);

                        var parts = [];
                        for (var index in languages) {
                            var language = languages[index];
                            var item = data[language];
                            parts.push({
                                type: options.type,
                                title: title,
                                language: item.lang,
                                content: item.text,
                                datasource: datasource_label,
                            });
                        };

                        // Render HTML content for single or multiple languages.
                        var template_multi = require('./fulltext-multi.html');
                        html_content = template_multi({identifier: identifier, items: parts});
                        content_element.html(html_content);

                    }

                    _this.setup_fulltext_tools(content_element);

                    if (navigatorApp.keywords) {
                        navigatorApp.keywords.highlight($(content_element).find('*'));
                    } else {
                        console.warn('Keywords subsystem not started. Keyword highlighting not available.')
                    }
                }
            }).fail(function(data) {
                log('Fetching fulltext for document failed:', data);
                _this.indicate_activity(container, false);
                if (data && data.html) {
                    content_element.html(template_single({
                        title: title,
                        content: data.html,
                        language: undefined,
                        datasource: undefined,
                    }));
                }
            });
        }

    },

    setup_fulltext_tools: function(container) {
        var _this = this;
        // Setup more button event handlers.
        var elements = container.find('*[data-component="nataraja"] a');
        elements.off('click');
        elements.on('click', function (event) {
            event.preventDefault();
            //event.stopPropagation();

            // Find out which comparison action has been clicked
            // and forward this information to Nataraja.
            var action = $(this).data('action');
            var text_element = $(this).closest('*[data-area="fulltext"]').find('*[data-area="text"]');
            if (action == 'comparison-select-left') {
                _this.nataraja.select_left(text_element);
            } else if (action == 'comparison-select-right') {
                _this.nataraja.select_right(text_element);
            }
        });
    },

    // TODO: Move to family.js
    display_family: function(document, container, view_type) {

        var document_number = document.get_publication_number('epodoc');
        if (document.get('datasource') == 'ificlaims') {
            document_number = document.get_publication_number('docdb');
        }

        // compute data collection and view class
        var view_class;
        var family_collection;
        if (view_type == 'compact') {
            family_collection = new OpsFamilyCollection(null, {document_number: document_number});
            view_class = OpsFamilyCompactCollectionView;
        } else if (view_type == 'verbose') {
            family_collection = new OpsFamilyCollection(null, {document_number: document_number});
            view_class = OpsFamilyVerboseCollectionView;
        } else if (view_type == 'citations') {
            family_collection = new OpsFamilyCollection(null, {document_number: document_number, constituents: 'biblio'});
            view_class = OpsFamilyCitationsCollectionView;
        }


        // create marionette region at dom element for displaying family information
        var content_element = container.find('.document-details-content');
        var family_region = new Backbone.Marionette.Region({
            el: content_element
        });

        if (!family_collection || !view_class) {
            family_region.close();
            content_element.empty();
            return;
        }

        // link family collection to its view and show view in region
        var view = new view_class({
            collection: family_collection,
        })
        //family_region.show(view);

        // finally, fetch data to fill the collection
        var _this = this;
        _this.indicate_activity(container, true);
        family_collection.fetch().then(function() {
            _this.indicate_activity(container, false);
            family_region.show(view);
            //log('family_collection:', family_collection);

        }).fail(function() {

            _this.indicate_activity(container, false);

            // indicate family acquistion failed
            FamilyFailedView = Backbone.Marionette.ItemView.extend({
                render : function (){
                    this.$el.append('No family information available.');
                }
            });
            family_region.show(new FamilyFailedView());
        });

    },

    indicate_activity: function(container, active) {
        var spinner = container.find('.document-details-spinner');
        if (active) {
            spinner.show();

        } else {
            spinner.hide();
        }
    },

    get_citations_environment_button: function(model, options) {
        return citations_environment_button(model, options);
    },

});

DocumentCarouselController = Marionette.Controller.extend({

    initialize: function(options) {
        console.log('DocumentCarouselController.initialize');
    },

    setup_ui: function() {

        var _this = this;

        // ------------------------------------------
        //   drawings carousel
        // ------------------------------------------

        // turn slideshow off
        $('.drawings-carousel').carousel({
            interval: null
        });

        // update page numbers after sliding
        $('.drawings-carousel').on('slid', function(event) {
            _this.update_carousel_metadata(this);
        });

        // Load drawing when pressing respective navigation button
        function drawing_navigate(context, offset) {
            var carousel = $(context).closest('.ops-collection-entry').find('.drawings-carousel');
            _this.carousel_load_drawing(carousel, offset);
        }

        // Navigate to previous drawing
        $('.drawings-carousel .carousel-control.left').on('click', function(event) {

            // Prevent over-navigation to the previous drawing if there's just one item in the collection
            var carousel_items = $(this).closest('.ops-collection-entry').find('.drawings-carousel').find('.carousel-inner');
            var item_count = carousel_items.find('div').length;
            if (item_count <= 1) {
                event.preventDefault();
                event.stopPropagation();
            }

            // TODO: Use same navigation utility function like the "next" button on the right hand side
            //drawing_navigate(this, -1);

        });

        // Navigate to next drawing
        $('.drawings-carousel .carousel-control.right').on('click', function(event) {
            drawing_navigate(this, +1);
        });

        // Rotate drawings clockwise in steps of 90 degrees
        $('.carousel-control.rotate').on('click', function(event, direction) {
            event.preventDefault();
            event.stopPropagation();

            // Find active drawing
            var carousel = $(this).closest('.ops-collection-entry').find('.drawings-carousel');
            var active_image = carousel.find('.carousel-inner .item.active img').first();
            //log('active_image:', active_image);

            // Compute relative rotation
            var rotation = 90;
            if (direction == 'counter') {
                rotation = -90;
            }

            // Rotate image
            var angle = active_image.data('angle') || 0;
            angle = (angle + rotation) % 360;
            active_image.data('angle', angle);
            active_image.css('transform','rotate(' + angle + 'deg)');

        });

        // lazy-initialize carousel to fetch totalcount from api and display page numbers
        $('.drawings-carousel').each(function(idx, carousel) {
            var carousel = $(carousel);

            // "number of drawings" is required to limit the upper page bound,
            // inquire it from image information metadata and save it as metadata into the corresponding dom element
            var totalcount = carousel.data('totalcount');
            if (!totalcount) {
                var document_number = carousel.closest('.ops-collection-entry').data('document-number');
                if (!document_number) {
                    console.warn("document-number could not be found, won't proceed loading items into carousel");
                    return;
                }
                //console.log(document_number);

                // TODO: refactor to models/ops.js
                var image_info_url = _.template('/api/ops/<%= patent %>/image/info')({ patent: document_number });
                //log('image_info_url:', image_info_url);

                $.ajax({
                    url: image_info_url,
                    async: true,

                }).then(function(payload) {
                    if (payload) {
                        totalcount = payload['META']['drawing-total-count'];
                        //console.log('drawing count: ' + totalcount);
                        carousel.data('totalcount', totalcount);
                        _this.update_carousel_metadata(carousel);
                    }

                }).catch(function(error) {
                    var error_data = xhr_decode_error(error);
                    console.warn('No image information for ' + document_number + ':', error_data.name, error_data);
                });
                carousel.data('totalcount', totalcount);
                _this.update_carousel_metadata(carousel);
            }

        });


        // hide broken drawing images
        var images = $('.drawings-carousel').find('img');
        images.off('error');
        images.on('error', function() {
            $(this).hide();
            var image_placeholder = '<br/><blockquote class="text-center" style="min-height: 300px"><br/><br/><br/><br/><br/><br/>No image</blockquote>';
            $(this).closest('.carousel').hide().parent().find('.drawing-info').html(image_placeholder);
        }); //.attr("src", "missing.png");

    },

    // Update number of current drawing and totalcount in user interface
    update_carousel_metadata: function(carousel) {

        var container = $(carousel).closest('.ops-collection-entry');
        var navigation_controls = $(carousel).find('.carousel-control.left, .carousel-control.right');

        navigation_controls.show();

        // Current drawing number
        var carousel_data = $(carousel).data('carousel');
        if (carousel_data) {
            var page = carousel_data.getActiveIndex() + 1;
            container.find('.drawing-number').text(page);
        }

        // Total count of all drawings
        var totalcount = $(carousel).data('totalcount');
        if (totalcount) {
            container.find('.drawing-totalcount').text('/' + totalcount);
        }

        // Hide previous/next navigation buttons if there is no totalcount
        if (!totalcount || totalcount == 1) {
            navigation_controls.hide();
        }
    },

    carousel_load_drawing: function(carousel, offset) {

        var carousel_items = carousel.find('.carousel-inner');

        var item_index_current = carousel_items.find('div.active').index() + 1;
        var item_index_new = item_index_current + offset;
        var item_count = carousel_items.find('div').length;

        // Use regular page flip mechanics when not on the last page,
        // i.e. don't manifest a new carousel item
        if (item_index_current != item_count) return;

        // "number of drawings" is required to limit the upper page bound
        var totalcount = carousel.data('totalcount');

        // skip if totalcount is invalid
        if (!totalcount) return;

        // skip if all drawings are already established
        if (item_count >= totalcount) return;


        // build a new carousel item from the last one
        var blueprint = $(carousel_items).children(':first').clone();
        var height = $(carousel_items).height();
        $(blueprint).removeClass('active');

        // manipulate nested img src: bump page number
        var img = $(blueprint).children('img');
        img.css('transform', 'inherit');
        var src = img.attr('src').replace(/\?page=.*/, '');
        src += '?page=' + (item_index_new);
        img.attr('src', src);
        //console.log(src);

        // Fix height-flickering of list entry when new drawing is lazy-loaded into carousel
        $(blueprint).attr('min-height', height);
        //$(blueprint).height(height);

        // add carousel item
        $(carousel_items).append(blueprint);

    },

});


PdfPanelController = Marionette.Controller.extend({

    initialize: function(options) {
        console.log('PdfPanelController.initialize');
    },

    setup_ui: function() {

        var _this = this;

        // pdf action button
        $(".pdf-open").on('click', function() {

            var patent_number = $(this).data('patent-number');
            var pdf_url = $(this).data('pdf-url');
            var pdf_page = 1;

            _this.pdf_set_headline(patent_number, pdf_page);
            _this.pdf_display('pdf', pdf_url, pdf_page);

            // pdf paging actions
            $("#pdf-previous").off();
            $("#pdf-previous").on('click', function() {
                if (pdf_page == 1) return;
                pdf_page -= 1;
                _this.pdf_set_headline(patent_number, pdf_page);
                _this.pdf_display('pdf', pdf_url, pdf_page);
            });
            $("#pdf-next").off();
            $("#pdf-next").on('click', function() {
                pdf_page += 1;
                _this.pdf_set_headline(patent_number, pdf_page);
                _this.pdf_display('pdf', pdf_url, pdf_page);
            });

        });

    },

    pdf_display: function(element_id, url, page) {
        // embed pdf object
        var pdf_object = new PDFObject({
            url: url + '?page=' + page,
            id: 'myPDF',
            pdfOpenParams: {
                navpanes: 0,
                toolbar: 0,
                statusbar: 0,
                view: 'FitB',
                //zoom: '100',
            },
        });
        pdf_object.embed(element_id);
    },

    pdf_set_headline: function(document_number, page) {
        var headline = document_number + ' Page ' + page;
        $(".modal-header #ops-pdf-modal-label").empty().append(headline);
    },

});



// setup plugin
navigatorApp.addInitializer(function(options) {
    this.document_base = new DocumentBaseController();
    this.document_details = new DocumentDetailsController();
    this.document_carousel = new DocumentCarouselController();
    this.listenTo(this, 'results:ready', function() {
        this.document_base.setup_ui();
        this.document_details.setup_ui();
        this.document_carousel.setup_ui();
    });
});
