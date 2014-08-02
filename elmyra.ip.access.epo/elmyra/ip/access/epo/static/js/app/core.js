// -*- coding: utf-8 -*-
// (c) 2013,2014 Andreas Motl, Elmyra UG

function indicate_activity(active) {
    if (active) {
        $('.idler').hide();
        $('.spinner').show();

    } else {
        $('.spinner').hide();
        $('.idler').show();
    }
}

function pdf_display(element_id, url, page) {
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
}

function pdf_set_headline(document_number, page) {
    var headline = document_number + ' Page ' + page;
    $(".modal-header #ops-pdf-modal-label").empty().append(headline);
}

function apply_highlighting() {
    // http://hslpicker.com/
    var styles = {
        yellow:     {backgroundColor: 'hsla( 60, 100%, 82%, 1)'},
        green:      {backgroundColor: 'hsla(118, 100%, 82%, 1)'},
        orange:     {backgroundColor: 'hsla( 16, 100%, 82%, 1)'},
        turquoise:  {backgroundColor: 'hsla(174, 100%, 82%, 1)'},
        blue:       {backgroundColor: 'hsla(195, 100%, 82%, 1)'},
        violet:     {backgroundColor: 'hsla(247, 100%, 82%, 1)'},
        magenta:    {backgroundColor: 'hsla(315, 100%, 82%, 1)'},
    };
    var style_queue = ['yellow', 'green', 'orange', 'turquoise', 'blue', 'violet', 'magenta'];
    var style_queue_work;
    _.each(opsChooserApp.metadata.get('keywords'), function(keyword) {
        log('keyword:', keyword);
        if (keyword) {

            // refill style queue
            if (_.isEmpty(style_queue_work)) {
                style_queue_work = style_queue.slice(0);
            }

            // get next style available
            var style_name = style_queue_work.shift();
            var style = styles[style_name];

            var class_name = 'highlight-' + style_name;

            // perform highlighting
            $('.keyword').highlight(keyword, {className: 'highlight-base ' + class_name, wholeWords: true, minLength: 3});

            // apply style
            $('.' + class_name).css(style);
        }
    });
}

function hide_elements() {

    // hide all navigational- and action-elements when in print mode
    var MODE_PRINT = opsChooserApp.config.get('mode') == 'print';
    if (MODE_PRINT) {
        $('.do-not-print').hide();
    }

    // hide all navigational- and action-elements when in view-only mode
    var MODE_LIVEVIEW = opsChooserApp.config.get('mode') == 'liveview';
    if (MODE_LIVEVIEW) {
        $('.non-liveview').hide();
    }
}

function listview_bind_actions() {

    hide_elements();

    var MODE_PRINT = opsChooserApp.config.get('mode') == 'print';
    if (MODE_PRINT) {
        return;
    }

    //console.log('listview_bind_actions');


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

    // apply jquery-keyword-highlight
    apply_highlighting();

    // popovers
    // TODO: rename to just "popover" or similar, since not just buttons may have popovers
    $('.btn-popover').popover();

    // tooltips
    // TODO: rename to just "tooltip" or similar, since tooltipping is universal
    $('.inid-tooltip').tooltip();

    // pdf action button
    $(".pdf-open").click(function() {

        var patent_number = $(this).data('patent-number');
        var pdf_url = $(this).data('pdf-url');
        var pdf_page = 1;

        pdf_set_headline(patent_number, pdf_page);
        pdf_display('pdf', pdf_url, pdf_page);

        // pdf paging actions
        $("#pdf-previous").unbind();
        $("#pdf-previous").click(function() {
            if (pdf_page == 1) return;
            pdf_page -= 1;
            pdf_set_headline(patent_number, pdf_page);
            pdf_display('pdf', pdf_url, pdf_page);
        });
        $("#pdf-next").unbind();
        $("#pdf-next").click(function() {
            pdf_page += 1;
            pdf_set_headline(patent_number, pdf_page);
            pdf_display('pdf', pdf_url, pdf_page);
        });

    });

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


    // ------------------------------------------
    //   drawings carousel
    // ------------------------------------------

    // turn slideshow off
    $('.drawings-carousel').carousel({
        interval: null
    });

    // update drawing-number and -totalcount in ui
    function update_carousel(carousel) {

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
    }

    // update page numbers after sliding
    $('.drawings-carousel').bind('slid', function(event) {
        update_carousel(this);
    });

    // bind carousel navigation buttons (left, right)
    var carousel_button_more = $('.drawings-carousel .carousel-control.right');
    carousel_button_more.click(function(event) {

        /*
         * dynamically load more drawings into the carousel,
         * until maximum is reached
         *
         */

        var carousel = $(this).closest('.ops-collection-entry').find('.drawings-carousel');
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
            var image_info_url = _.template('/api/ops/<%= patent %>/image/info')({ patent: document_number });
            //console.log(image_info_url);

            $.ajax({url: image_info_url, async: true}).success(function(payload) {
                if (payload) {
                    totalcount = payload['META']['drawing-total-count'];
                    //console.log('drawing count: ' + totalcount);
                    carousel.data('totalcount', totalcount);
                    update_carousel(carousel);
                }
            }).error(function(error) {
                console.warn('Error while fetching total count of drawings', error);
            });
            carousel.data('totalcount', totalcount);
            update_carousel(carousel);
        }

    });


    // hide broken drawing images
    var images = $('.drawings-carousel').find('img');
    images.error(function() {
        $(this).hide();
        var image_placeholder = '<br/><blockquote class="text-center" style="min-height: 300px"><br/><br/><br/><br/><br/><br/>No image</blockquote>';
        $(this).closest('.carousel').hide().parent().find('.drawing-info').html(image_placeholder);
    }); //.attr("src", "missing.png");


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


    // --------------------------------------------
    //   toggle detail view (description, claims)
    // --------------------------------------------
    $('button[data-toggle="tab"]').on('show', function (e) {
        // e.target // activated tab
        // e.relatedTarget // previous tab

        var content_container = $($(e.target).attr('href'));

        var document_number = $(this).data('document-number');
        var details_type = $(this).data('document-details-type');
        if (details_type == 'description') {
            display_description(document_number, content_container);
        } else if (details_type == 'claims') {
            display_claims(document_number, content_container);
        }

        // fix missing popover after switching inline detail view
        $('.btn-popover').popover();
    })

}

function display_description(document_number, container) {

    var content_element = container.find('.document-details-content')[0];
    var language_element = container.find('.document-details-language')[0];

    if (content_element) {

        // TODO: move to ops.js
        var url = _.template('/api/ops/<%= document_number %>/description')({ document_number: document_number});
        $.ajax({url: url, async: true}).success(function(payload) {
            if (payload) {
                var description = payload['ops:world-patent-data']['ftxt:fulltext-documents']['ftxt:fulltext-document']['description'];
                console.log('description', document_number, description);

                // TODO: unify with display_claims
                var content_parts = _(to_list(description.p)).map(function(item) {
                    return '<p>' + _(item['$']).escape().replace(/\n/g, '<br/><br/>') + '</p>';
                });
                var content_text = content_parts.join('\n');
                $(content_element).html(content_text);
                $(language_element).html('[' + description['@lang'] + ']');
                apply_highlighting();
            }
        }).error(function(error) {
            console.warn('Error while fetching description', error);
        });

    }

}

function display_claims(document_number, container) {

    var content_element = container.find('.document-details-content')[0];
    var language_element = container.find('.document-details-language')[0];

    if (content_element) {

        // TODO: move to ops.js
        var url = _.template('/api/ops/<%= document_number %>/claims')({ document_number: document_number});
        $.ajax({url: url, async: true}).success(function(payload) {
            if (payload) {
                var claims = payload['ops:world-patent-data']['ftxt:fulltext-documents']['ftxt:fulltext-document']['claims'];
                console.log('claims', document_number, claims);

                // TODO: unify with display_description
                var content_parts = _(to_list(claims['claim']['claim-text'])).map(function(item) {
                    return '<p>' + _(item['$']).escape().replace(/\n/g, '<br/>') + '</p>';
                });
                var content_text = content_parts.join('\n');
                $(content_element).html(content_text);
                $(language_element).html('[' + claims['@lang'] + ']');
                apply_highlighting();
            }
        }).error(function(error) {
                console.warn('Error while fetching claims', error);
            });

    }

}

function reset_content(options) {
    $('#alert-area').empty();
    $('#info-area').empty();
    $('#pagination-info').hide();
    options = options || {};
    if (!options.keep_pager) {
        $('.pager-area').hide();
    }
    if (options.documents) {
        opsChooserApp.documents.reset();
    }
}

function getconfig(name, options) {
    options = options || {};
    var label = opsChooserApp.config.get(name);
    if (label) {
        if (options.before) {
            label = options.before + label;
        }
        if (options.after) {
            label = label + options.after;
        }
    }
    return label;
}

function boot_application() {

    console.log('boot_application');

    // ------------------------------------------
    //   intro
    // ------------------------------------------

    // initialize content which still resides on page level (i.e. no template yet)
    $('#query').val(opsChooserApp.config.get('query'));
    $('#ui-title').html(getconfig('setting.ui.page.title'));
    $('#ui-subtitle').html(getconfig('setting.ui.page.subtitle'));
    $('#ui-statusline').html(getconfig('setting.ui.page.statusline'));
    $('#ui-productname').html(getconfig('setting.ui.productname'));
    $('#ui-footer').html(getconfig('setting.ui.page.footer', {after: '<br/>'}));
    $('#ui-footer-version').html(getconfig('setting.ui.version', {after: '<br/>'}));

    // hide pagination- and metadata-area to start from scratch
    reset_content();


    // ------------------------------------------
    //   generic
    // ------------------------------------------

    // apply popovers to all desired buttons
    $('.btn-popover').popover();

    opsChooserApp.ui.setup_text_tools();

    // defaults for notification popups
    $.notify.defaults({className: 'info', showAnimation: 'fadeIn', hideAnimation: 'fadeOut', autoHideDelay: 4000, showDuration: 300});



    // -------------------------------------------------
    //   propagate opaque error messages to alert area
    // -------------------------------------------------
    var status = opsChooserApp.config.get('opaque.meta.status');
    if (status == 'error') {
        var errors = opsChooserApp.config.get('opaque.meta.errors');
        _.each(errors, function(error) {

            if (error.location == 'JSON Web Token' && error.description == 'expired') {
                error.description =
                    'We are sorry, it looks like the validity time of this link has expired at ' + error.jwt_expiry_iso + '.' +
                    '<br/><br/>' +
                    'Please contact us at <a href="mailto:support@elmyra.de">support@elmyra.de</a> for any commercial plans.';
            }
            if (error.location == 'JSON Web Signature') {
                error.description = 'It looks like the token used to encode this request is invalid.' + ' (' + error.description + ')'
            }

            var tpl = _.template($('#cornice-error-template').html());
            var alert_html = tpl(error);
            $('#alert-area').append(alert_html);
        });
    }



    // ------------------------------------------
    //   logout button
    // ------------------------------------------
    if (opsChooserApp.config.get('mode') == 'liveview') {
        $('.logout-button').hide();
    }


    // ------------------------------------------
    //   cql query area
    // ------------------------------------------

    // set cursor to end of query string, also focuses element
    //$('#query').caret($('#query').val().length);


    /*
    // intercept and reformat clipboard content
    $("#query").on("paste", function(e) {

        // only run interceptor if content of target element is empty
        if ($(this).val()) return;

        e.preventDefault();

        var text = (e.originalEvent || e).clipboardData.getData('text');

    });
    */


    // ------------------------------------------
    //   cql field chooser
    // ------------------------------------------
    // propagate "datasource" query parameter
    var datasource = opsChooserApp.config.get('datasource');
    if (datasource) {
        opsChooserApp.set_datasource(datasource);
    }


    // ------------------------------------------
    //   online help
    // ------------------------------------------

    // transform query: open modal dialog to choose transformation kind
    $('#link-help').click(function() {

        // v1: modal dialog
        //$('#help-modal').modal('show');

        // v2: different page
        var baseurl = opsChooserApp.config.get('baseurl');
        var url = baseurl + '/help';
        $(this).attr('href', url);
    });

    opsChooserApp.trigger('application:ready');

    hide_elements();

}

