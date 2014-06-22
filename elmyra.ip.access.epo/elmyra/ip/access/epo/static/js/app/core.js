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
    _.each(opsChooserApp.metadata.get('keywords'), function(keyword) {
        //console.log('keyword: ' + keyword);
        $('.keyword').keywordHighlight({
            keyword: keyword,
            caseSensitive: 'false',
            contains: 'true',
        });
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

        // v1
        /*
        event.preventDefault();
        var attr = $(this).data('query-attribute');
        var val = $(this).data('query-value');
        var query = attr + '=' + val;
        opsChooserApp.send_query(query);
        */

        // v2
        // propagate state of (mode, context, project, datasource=ops) into query parameters

        // build state payload
        var state = {
            mode: opsChooserApp.config.get('mode'),
            context: opsChooserApp.config.get('context'),
            project: opsChooserApp.config.get('project'),
            datasource: 'ops',
        };
        if (opsChooserApp.project) {
            state.project = opsChooserApp.project.get('name');
        }

        var href = $(this).attr('href');
        var url = $.url(href);
        var params = url.param();
        _(params).extend(state);

        // serialize state into opaque parameter token when in liveview
        if (opsChooserApp.config.get('isviewer')) {
            var _this = this;
            opaque_param(params).then(function(opaque_query) {
                $(_this).attr('href', '?' + opaque_query);
            })

        // serialize state into regular query parameters otherwise
        } else {
            if (_.string.contains(href, '?')) {
                href += '&';
            } else {
                href += '?';
            }
            href += jQuery.param(state);
            $(this).attr('href', href);
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

    // auto-shorten some texts
    $(".very-short").shorten({showChars: 5, moreText: 'more', lessText: 'less'});

    // defaults for notification popups
    $.notify.defaults({className: 'info', showAnimation: 'fadeIn', hideAnimation: 'fadeOut', autoHideDelay: 4000, showDuration: 300});


    // ------------------------------------------
    //   cql query area
    // ------------------------------------------

    // set cursor to end of query string, also focuses element
    //$('#query').caret($('#query').val().length);

    // application action: perform search
    $('.btn-query-perform').click(function() {
        opsChooserApp.perform_search({reviewmode: false});
    });


    // ------------------------------------------
    //   datasource selector
    // ------------------------------------------

    // switch cql field chooser when selecting datasource
    // TODO: do it properly on the configuration data model
    $('#datasource').on('click', '.btn', function(event) {
        opsChooserApp.set_datasource($(this).data('value'));
    });



    // ------------------------------------------
    //   hotkeys
    // ------------------------------------------

    // submit on meta+enter
    $('#query').on('keydown', null, 'meta+return', function() {
        opsChooserApp.perform_search({reviewmode: false});
    });
    $('#query').on('keydown', null, 'ctrl+return', function(event) {
        opsChooserApp.perform_search({reviewmode: false});
    });

    // select datasource
    _([document, '#query']).each(function (selector) {
        $(selector).on('keydown', null, 'ctrl+shift+e', function(event) {
            $('#datasource button[data-value="ops"]').button('toggle');
            opsChooserApp.set_datasource('ops');
        });
        $(selector).on('keydown', null, 'ctrl+shift+d', function(event) {
            $('#datasource button[data-value="depatisnet"]').button('toggle');
            opsChooserApp.set_datasource('depatisnet');
        });
        $(selector).on('keydown', null, 'ctrl+shift+r', function(event) {
            opsChooserApp.basketModel.review();
        });
    });

    // add/remove/rate the document in viewport to/from basket
    $(document).on('keydown', null, '+', function() {
        opsChooserApp.viewport_document_add_basket();
    });
    $(document).on('keydown', null, 'insert', function() {
        opsChooserApp.viewport_document_rate(1);
    });

    $(document).on('keydown', null, '-', function() {
        opsChooserApp.viewport_document_remove_basket();
    });
    $(document).on('keydown', null, 'r', function() {
        opsChooserApp.viewport_document_remove_basket();
    });
    $(document).on('keydown', null, 'del', function() {
        opsChooserApp.viewport_document_remove_basket();
    });
    $(document).on('keydown', null, 'ctrl+d', function() {
        opsChooserApp.viewport_document_remove_basket();
    });

    $(document).on('keydown', null, '0', function() {
        opsChooserApp.viewport_document_rate(null, true);
    });
    $(document).on('keydown', null, 'd', function() {
        opsChooserApp.viewport_document_rate(null, true);
    });
    $(document).on('keydown', null, '1', function() {
        opsChooserApp.viewport_document_rate(1);
    });
    $(document).on('keydown', null, '2', function() {
        opsChooserApp.viewport_document_rate(2);
    });
    $(document).on('keydown', null, '3', function() {
        opsChooserApp.viewport_document_rate(3);
    });


    // snap scrolling to our items
    $(document).on('keydown', null, null, function(event) {

        if (event.keyCode == 32 && event.target.localName == 'body') {
            event.preventDefault();

            // scroll to the best next target element
            if (event.shiftKey == false) {
                scroll_smooth(mainlist_next_element());

                // scroll to the best previous target element
            } else if (event.shiftKey == true) {
                scroll_smooth(mainlist_previous_element());
            }

        }
    });
    $(document).on('keydown', null, 'pagedown', function(event) {
        event.preventDefault();
        scroll_smooth(mainlist_next_element());
    });
    $(document).on('keydown', null, 'pageup', function(event) {
        event.preventDefault();
        scroll_smooth(mainlist_previous_element());
    });


    // navigate the Biblio, Desc, Claims with left/right arrow keys
    $(document).on('keydown', null, 'right', function(event) {
        event.preventDefault();
        var tab_chooser = $('.ops-collection-entry:in-viewport').find('.document-actions .document-tab-chooser').first();
        var active_button = tab_chooser.find('button.active');
        var next = active_button.next('button');
        if (!next.length) {
            next = active_button.siblings('button').first();
        }
        next.tab('show');
    });
    $(document).on('keydown', null, 'left', function(event) {
        event.preventDefault();
        var tab_chooser = $('.ops-collection-entry:in-viewport').find('.document-actions .document-tab-chooser').first();
        var active_button = tab_chooser.find('button.active');
        var next = active_button.prev('button');
        if (!next.length) {
            next = active_button.siblings('button').last();
        }
        next.tab('show');
    });


    // navigate the carousel with shift+left/right arrow keys
    $(document).on('keydown', null, 'shift+right', function(event) {
        event.preventDefault();
        var drawings_carousel = $('.ops-collection-entry:in-viewport').find('.drawings-carousel').first();
        var carousel_button_more = drawings_carousel.find('.carousel-control.right');
        carousel_button_more.trigger('click');
    });
    $(document).on('keydown', null, 'shift+left', function(event) {
        event.preventDefault();
        var drawings_carousel = $('.ops-collection-entry:in-viewport').find('.drawings-carousel').first();
        var carousel_button_more = drawings_carousel.find('.carousel-control.left');
        carousel_button_more.trigger('click');
    });


    // open pdf on "p"
    $(document).on('keydown', null, 'shift+p', function(event) {
        event.preventDefault();
        var anchor = $('.ops-collection-entry:in-viewport').find('a.anchor-pdf-ops');
        anchor[0].click();
    });


    // links to various patent offices
    // open Espacenet on "shift+e"
    $(document).on('keydown', null, 'shift+e', function(event) {
        event.preventDefault();
        var anchor = $('.ops-collection-entry:in-viewport').find('a.anchor-biblio-espacenet');
        anchor[0].click();
    });
    // open DEPATISnet on "shift+d"
    $(document).on('keydown', null, 'shift+d', function(event) {
        event.preventDefault();
        var anchor = $('.ops-collection-entry:in-viewport').find('a.anchor-biblio-depatisnet');
        anchor[0].click();
    });
    // open epo register information on "shift+alt+e"
    $(document).on('keydown', null, 'alt+shift+e', function(event) {
        event.preventDefault();
        $('.ops-collection-entry:in-viewport').find('a.anchor-register-epo')[0].click();
    });
    // open dpma register information on "shift+alt+d"
    $(document).on('keydown', null, 'alt+shift+d', function(event) {
        event.preventDefault();
        $('.ops-collection-entry:in-viewport').find('a.anchor-register-dpma')[0].click();
    });
    // open ccd on "shift+c"
    $(document).on('keydown', null, 'shift+c', function(event) {
        event.preventDefault();
        $('.ops-collection-entry:in-viewport').find('a.anchor-ccd')[0].click();
    });


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
    //   cql query area action tools
    // ------------------------------------------

    // trash icon clears the whole content
    $('#btn-query-clear').click(function() {
        $('#query').val('').focus();
    });

    // transform query: open modal dialog to choose transformation kind
    $('#btn-query-transform').click(function() {
        // TODO: this "$('#query').val().trim()" should be kept at a central place
        if ($('#query').val().trim()) {
            $('#clipboard-modifier-chooser').modal('show');
        }
    });

    // open query chooser
    $('#btn-query-history').click(function(e) {

        // setup select2 widget
        cql_history_chooser_setup();

        var opened = $('#cql-history-chooser').hasClass('open');
        var chooser_widget = $('#cql-history-chooser-select2');

        // if already opened, skip event propagation and just reopen the widget again
        if (opened) {
            e.preventDefault();
            e.stopPropagation();
            chooser_widget.select2('open');

        // open select2 widget *after* dropdown has been opened
        } else {
            // TODO: use "shown.bs.dropdown" event when migrating to bootstrap3
            setTimeout(function() {
                chooser_widget.select2('open');
            });
        }
    });


    // transform query: modifier kind selected in dialog
    $('.btn-clipboard-modifier').click(function() {

        // get field name and operator from dialog
        var modifier = $(this).data('modifier');
        var operator = $('#clipboard-modifier-operator').find('.btn.active').data('value') || 'OR';

        // close dialog
        $('#clipboard-modifier-chooser').modal('hide');

        // compute new query content
        var text = $('#query').val().trim();
        if (_.str.contains(text, '=')) {
            return;
        }
        var entries = text.split('\n');
        var query = _(entries).map(function(item) {
            return modifier + '=' + '"' + item + '"';
        }).join(' ' + operator + ' ');

        // set query content and focus element
        $('#query').val(query);
        $('#query').focus();

    });


    // ------------------------------------------
    //   cql query builder
    // ------------------------------------------
    $('.btn-cql-boolean').button();
    $('#cql-quick-operator').find('.btn-cql-boolean').click(function() {
        $('#query').focus();
    });
    $('.btn-cql-field').click(function() {

        var query = $('#query').val();
        var operator = $('#cql-quick-operator').find('.btn-cql-boolean.active').data('value');
        var attribute = $(this).data('value');

        var position = $('#query').caret();
        var do_op = false;
        var do_att = true;
        //console.log('position: ' + position);

        var leftchar;
        if (position != 0) {
            do_op = true;

            // insert nothing if we're right off an equals "="
            leftchar = query.substring(position - 1, position);
            //console.log('leftchar: ' + leftchar);
            if (leftchar == '=') {
                do_op = false;
                do_att = false;
            }

            // don't insert operation if there's already one left of the cursor
            var fiveleftchar = query.substring(position - 5, position).toLowerCase();
            //console.log('fiveleftchar: ' + fiveleftchar);
            if (_.string.contains(fiveleftchar, 'and') || _.string.contains(fiveleftchar, 'or')) {
                do_op = false;
            }

        }

        // manipulate query by inserting relevant
        // parts at the current cursor position
        var leftspace = (!leftchar || leftchar == ' ') ? '' : ' ';

        if (do_op)
            $('#query').caret(leftspace + operator);
        if (do_att)
            $('#query').caret((do_op ? ' ' : leftspace) + attribute);

        $('#query').focus();
    });


    // ------------------------------------------
    //   cql field chooser
    // ------------------------------------------
    // propagate "datasource" query parameter
    var datasource = opsChooserApp.config.get('datasource')
    if (datasource) {
        opsChooserApp.set_datasource(datasource);
    }


    // ------------------------------------------
    //   online help
    // ------------------------------------------

    // transform query: open modal dialog to choose transformation kind
    $('#link-help').click(function() {
        $('#help-modal').modal('show');
    });

    opsChooserApp.trigger('application:ready');

    hide_elements();

}

// compute the best next list item
function mainlist_next_element() {
    var target;
    var origin = $('.ops-collection-entry:in-viewport');
    if ($(window).scrollTop() < origin.offset().top) {
        target = origin;
    } else {
        var target = origin.closest('.ops-collection-entry').last();
        if (target[0] === origin[0]) {
            target = $('.ops-collection-entry:below-the-fold').first();
        }
    }
    return target;
}

// compute the best previous list item
function mainlist_previous_element() {
    var target;
    var origin = $('.ops-collection-entry:in-viewport');
    if ($(window).scrollTop() > origin.offset().top) {
        target = origin;
    } else {
        var target = origin.closest('.ops-collection-entry').first();
        if (target[0] === origin[0]) {
            target = $('.ops-collection-entry:above-the-top').last();
        }
    }
    return target;
}

// perform animated scrolling
function scroll_smooth(target) {
    if ($(target).offset()) {
        $('html, body').animate({
            scrollTop: $(target).offset().top
        }, 500);
    }
}


function cql_field_chooser_get_data(datasource) {
    if (datasource == 'ops') {
        return OPS_CQL_FIELDS;

    } else if (datasource == 'depatisnet') {
        return DEPATISNET_CQL_FIELDS;

    } else {
        return [];

    }
}

function cql_field_chooser_setup() {
    var datasource = opsChooserApp.get_datasource();
    if (!datasource || datasource == 'review') {
        var container = $('#cql-field-chooser')[0].previousSibling;
        $(container).hide();
        return;
    }
    var data = cql_field_chooser_get_data(datasource);
    $('#cql-field-chooser').select2({
        placeholder: 'CQL field symbols' + ' (' + datasource + ')',
        data: { results: data },
        dropdownCssClass: "bigdrop",
        escapeMarkup: function(text) { return text; },
    });
    $('#cql-field-chooser').on('change', function(event) {

        var value = $(this).val();
        if (!value) return;

        //console.log(value);

        var query = $('#query').val();
        var position = $('#query').caret();
        var leftchar = query.substring(position - 1, position);

        // skip insert if we're right behind a "="
        if (leftchar == '=') return;

        // insert space before new field if there is none and we're not at the beginning
        if (leftchar != ' ' && position != 0) value = ' ' + value;

        $('#query').caret(value + '=');
        $(this).data('select2').clear();

    });

}

function cql_history_chooser_get_data() {
    var queries = opsChooserApp.project.get('queries');
    var chooser_data = _(queries).unique().map(function(query) {
        return { id: query, text: query };
    });
    return chooser_data;
}

function cql_history_chooser_setup() {
    var projectname = opsChooserApp.project.get('name');
    var data = cql_history_chooser_get_data();

    var chooser_widget = $('#cql-history-chooser-select2');

    // initialize cql history chooser
    chooser_widget.select2({
        placeholder: 'CQL history' + ' (' + projectname + ')',
        data: { results: data },
        dropdownCssClass: "bigdrop",
        escapeMarkup: function(text) { return text; },
    });

    // when query was selected, put it into cql query input field
    chooser_widget.unbind('change');
    chooser_widget.on('change', function(event) {

        $(this).unbind('change');

        var value = $(this).val();
        if (value) {

            // HACK: cut away suffix
            // TODO: move to QueryModel
            if (_.string.endsWith(value, '(ops)')) {
                opsChooserApp.set_datasource('ops');
            } else if (_.string.endsWith(value, '(depatisnet)')) {
                opsChooserApp.set_datasource('depatisnet');
            }
            value = value.replace(' (ops)', '').replace(' (depatisnet)', '');

            $('#query').val(value);
        }

        // destroy widget and close dropdown container
        $(this).data('select2').destroy();
        $(this).dropdown().toggle();

    });

}
