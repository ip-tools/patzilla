// -*- coding: utf-8 -*-
// (c) 2014 Andreas Motl, Elmyra UG

DocumentBaseController = Marionette.Controller.extend({

    initialize: function(options) {
        console.log('DocumentBaseController.initialize');
    },

    setup_ui: function() {

        // ------------------------------------------
        //   element visibility
        // ------------------------------------------
        opsChooserApp.ui.do_element_visibility();


        // ------------------------------------------
        //   print mode
        // ------------------------------------------
        var MODE_PRINT = opsChooserApp.config.get('mode') == 'print';
        if (MODE_PRINT) {
            return;
        }


        // ------------------------------------------
        //   metadata area
        // ------------------------------------------

        // shorten cql query string
        $(".cql-query").shorten({showChars: 125, moreText: 'more', lessText: 'less'});

        // apply autonumeric formatting
        $('#result-count-total').autoNumeric('init', {mDec: 0});


        // ------------------------------------------
        //   second pagination at bottom
        // ------------------------------------------
        $(opsChooserApp.paginationViewBottom.el).show();


        // ------------------------------------------
        //   result list
        // ------------------------------------------
        opsChooserApp.basket_bind_actions();

        // use jquery.shorten on "abstract" text
        $(".abstract").shorten({showChars: 2000, moreText: 'more', lessText: 'less'});

        // popovers
        // TODO: rename to just "popover" or similar, since not just buttons may have popovers
        $('.btn-popover').popover();

        // tooltips
        // TODO: rename to just "tooltip" or similar, since tooltipping is universal
        $('.inid-tooltip').tooltip();


        // run search actions when clicking query-links
        $(".query-link").unbind('click');
        $(".query-link").on('click', function(event) {

            var href = $(this).attr('href');
            var params = opsChooserApp.permalink.query_parameters_viewstate(href);

            // regardless where the query originates from (e.g. datasource=review),
            // requests for query-links need switching to ops
            params['datasource'] = 'ops';

            // debugging
            //opsChooserApp.config.set('isviewer', true);

            // when in liveview, scrumble database query and viewstate parameters into opaque parameter token
            if (opsChooserApp.config.get('isviewer')) {

                // nail to liveview mode in any case
                params['mode'] = 'liveview';

                // compute opaque parameter token and reset href
                var _this = this;
                opaque_param(params).then(function(opaque_query) {
                    $(_this).attr('href', '?' + opaque_query);
                })

                // serialize state into regular query parameters otherwise
            } else {
                $(this).attr('href', '?' + jQuery.param(params));
            }

        });


        // lazy german abstract acquisition
        $('.abstract-acquire').on('click', function(event) {
            event.preventDefault();
            var lang = $(this).data('lang');
            var document = $(this).closest('.ops-collection-entry').prop('ops-document');
            $(this).after('<span class="abstract-acquire-spinner">&nbsp;&nbsp;<i class="icon-refresh icon-spin"></i></span>');

            var ft = opsChooserApp.document_details.get_fulltext(document);
            var _this = this;
            ft.get_abstract(lang).then(function(data) {
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
                var _tpl = _.template(embed_item_url, null, { interpolate: /\{\{(.+?)\}\}/g });
                var embed_real_url = _tpl({publication_number: document_number});

                // 2. create an iframe
                var iframe = '<iframe src="' + embed_real_url + '" class="container-fluid well" seamless="seamless" height2="200" width2="100%" style="min-height: 50%; min-width: 80%"/>';
                $(this).append(iframe);

            }
        });


        // Shortcut button for jumping to Family » Citations
        $('.family-citations-shortcut-button').unbind('click');
        $('.family-citations-shortcut-button').bind('click', function(event) {
            var container = $(this).closest('.ops-collection-entry')
            container.find('.document-details-chooser > button[data-toggle="tab"][data-details-type="family"]').tab('show');
            container.find('.family-chooser > button[data-toggle="tab"][data-view-type="citations"]').tab('show');
        });

    },

});


DocumentDetailsController = Marionette.Controller.extend({

    initialize: function(options) {
        console.log('DocumentDetailsController.initialize');
    },

    setup_ui: function() {

        var _this = this;

        // --------------------------------------------
        //   toggle detail view (description, claims)
        // --------------------------------------------
        // TODO: refactor to ops.js
        $('.document-details-chooser > button[data-toggle="tab"]').on('show', function (e) {

            // e.target // activated tab
            // e.relatedTarget // previous tab

            var container = $($(e.target).attr('href'));
            var details_type = $(this).data('details-type');

            var document = $(this).closest('.ops-collection-entry').prop('ops-document');

            if (document) {
                if (_(['claims', 'description']).contains(details_type)) {
                    var details = _this.get_fulltext_details(details_type, document);
                    _this.display_details(details, container);

                } else if (details_type == 'family') {

                    var family_chooser = $(container).find('.family-chooser');

                    // event handler
                    family_chooser.find('button[data-toggle="tab"]').on('show', function (e) {
                        var view_type = $(this).data('view-type');
                        _this.display_family(document, container, view_type);
                    });

                    // initial setup
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
        var clazz = OpsFulltext;
        var document_number = document.get_publication_number('epodoc');

        var country = document['@country'];
        if (_(['DE', 'US']).contains(country)) {
            clazz = DepatisConnectFulltext;
            document_number = document.get_publication_number('docdb');
        }

        return new clazz(document_number);
    },

    get_fulltext_details: function(details_type, document) {
        var ft = this.get_fulltext(document);
        if (details_type == 'description') {
            return ft.get_description();
        } else if (details_type == 'claims') {
            return ft.get_claims();
        }
    },

    display_details: function(details, container) {
        var _this = this;

        var content_element = container.find('.document-details-content');
        var language_element = container.find('.document-details-language');

        if (content_element) {
            this.indicate_activity(container, true);
            details.then(function(data) {
                _this.indicate_activity(container, false);
                if (data) {
                    $(content_element).html(data['html']);
                    data['lang'] && $(language_element).html('[' + data['lang'] + ']');
                    opsChooserApp.keywords.highlight($(content_element).find('*'));
                }
            });
        }

    },

    display_family: function(document, container, view_type) {

        var document_number = document.get_publication_number('epodoc');

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
        family_region.show(view);

        // finally, fetch data to fill the collection
        var _this = this;
        _this.indicate_activity(container, true);
        family_collection.fetch().then(function() {
            _this.indicate_activity(container, false);
            //log('family_collection:', family_collection);
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
        $('.drawings-carousel').bind('slid', function(event) {
            _this.update_carousel_metadata(this);
        });

        // fetch more drawings when triggering right navigation button
        var carousel_button_more = $('.drawings-carousel .carousel-control.right');
        carousel_button_more.click(function(event) {
            // dynamically load more drawings into the carousel, until maximum is reached
            var carousel = $(this).closest('.ops-collection-entry').find('.drawings-carousel');
            _this.carousel_fetch_next(carousel);
        });

        // lazy-initialize carousel to fetch totalcount from api and display page numbers
        $('.drawings-carousel').each(function(idx, carousel) {
            var carousel = $(carousel);

            // "number of drawings" is required to limit the upper page bound,
            // inquire it from image information metadata and save it as metadata into the corresponding dom element
            var totalcount = carousel.data('totalcount');
            if (!totalcount) {
                totalcount = 1;
                var document_number = carousel.closest('.ops-collection-entry').data('document-number');
                if (!document_number) {
                    console.warn("document-number could not be found, won't proceed loading items into carousel");
                    return;
                }
                //console.log(document_number);

                // TODO: refactor to models/ops.js
                var image_info_url = _.template('/api/ops/<%= patent %>/image/info')({ patent: document_number });
                //console.log(image_info_url);

                $.ajax({url: image_info_url, async: true}).success(function(payload) {
                    if (payload) {
                        totalcount = payload['META']['drawing-total-count'];
                        //console.log('drawing count: ' + totalcount);
                        carousel.data('totalcount', totalcount);
                        _this.update_carousel_metadata(carousel);
                    }
                }).error(function(error) {
                        console.warn('Error while fetching total count of drawings', error);
                    });
                carousel.data('totalcount', totalcount);
                _this.update_carousel_metadata(carousel);
            }

        });


        // hide broken drawing images
        var images = $('.drawings-carousel').find('img');
        images.error(function() {
            $(this).hide();
            var image_placeholder = '<br/><blockquote class="text-center" style="min-height: 300px"><br/><br/><br/><br/><br/><br/>No image</blockquote>';
            $(this).closest('.carousel').hide().parent().find('.drawing-info').html(image_placeholder);
        }); //.attr("src", "missing.png");

    },

    // update drawing-number and -totalcount in ui
    update_carousel_metadata: function(carousel) {

        var container = $(carousel).closest('.ops-collection-entry');

        // current drawing number
        var carousel_real = $(carousel).data('carousel');
        if (carousel_real) {
            var page = carousel_real.getActiveIndex() + 1;
            container.find('.drawing-number').text(page);
        }

        // number of all drawings
        //var carousel = container.find('.drawings-carousel');
        var totalcount = $(carousel).data('totalcount');
        if (totalcount)
            container.find('.drawing-totalcount').text('/' + totalcount);
    },

    carousel_fetch_next: function(carousel) {

        var carousel_items = carousel.find('.carousel-inner');

        var item_index = carousel_items.find('div.active').index() + 1;
        var item_count = carousel_items.find('div').length;


        // skip if we're not on the last page
        if (item_index != item_count) return;


        // "number of drawings" is required to limit the upper page bound,
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
        var src = img.attr('src').replace(/\?page=.*/, '');
        src += '?page=' + (item_index + 1);
        img.attr('src', src);
        //console.log(src);

        // fix height-flickering of list entry when new drawing is lazy-loaded into carousel
        $(blueprint).attr('min-height', height);
        $(blueprint).height(height);

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
        $(".pdf-open").click(function() {

            var patent_number = $(this).data('patent-number');
            var pdf_url = $(this).data('pdf-url');
            var pdf_page = 1;

            _this.pdf_set_headline(patent_number, pdf_page);
            _this.pdf_display('pdf', pdf_url, pdf_page);

            // pdf paging actions
            $("#pdf-previous").unbind();
            $("#pdf-previous").click(function() {
                if (pdf_page == 1) return;
                pdf_page -= 1;
                _this.pdf_set_headline(patent_number, pdf_page);
                _this.pdf_display('pdf', pdf_url, pdf_page);
            });
            $("#pdf-next").unbind();
            $("#pdf-next").click(function() {
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
opsChooserApp.addInitializer(function(options) {
    this.document_base = new DocumentBaseController();
    this.document_details = new DocumentDetailsController();
    this.document_carousel = new DocumentCarouselController();
    this.listenTo(this, 'results:ready', function() {
        this.document_base.setup_ui();
        this.document_details.setup_ui();
        this.document_carousel.setup_ui();
    });
});
