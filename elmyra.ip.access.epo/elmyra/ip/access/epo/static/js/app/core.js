// -*- coding: utf-8 -*-
// (c) 2013,2014 Andreas Motl, Elmyra UG

function indicate_activity(active) {
    if (active) {
        $('#idler').hide();
        $('#spinner').show();

    } else {
        $('#spinner').hide();
        $('#idler').show();
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

function listview_bind_actions() {

    // hide all navigational- and action-elements when in print mode
    if (PRINTMODE) {
        $('.do-not-print').hide();
        return;
    }

    // pager: create page size chooser
    $('.page-size-chooser ul').each(function(i, page_size_chooser) {
        $(this).empty();
        var self = this;
        var pagesize_choices = opsChooserApp.metadata.get('pagination_pagesize_choices');
        var pagesize_chosen = opsChooserApp.metadata.get('page_size');
        _(pagesize_choices).map(function(pagesize) {
            var icon = '';
            if (pagesize == pagesize_chosen) {
                icon = '<i class="icon-check"></i>';
            } else {
                icon = '<i class="icon-check-empty"></i>';
            }
            var entry = _.template('<li><a href="" data-value="<%= pagesize %>"><%= icon %> <%= pagesize %></a></li>')({pagesize: pagesize, icon: icon});
            $(self).append(entry);
        });
    });

    // pager: make links from page size chooser entries
    $('.page-size-chooser a').click(function() {
        var value = $(this).data('value');
        opsChooserApp.metadata.set('page_size', value);
        opsChooserApp.perform_search();
        return false;
    });

    // pager: create pagination entries
    $('.pagination ul').each(function(i, pagination) {
        $(this).empty();
        var self = this;
        var pagination_entry_count = opsChooserApp.metadata.get('pagination_entry_count');
        var page_size = opsChooserApp.metadata.get('page_size');
        _.range(1, pagination_entry_count * page_size, page_size).map(function(index) {
            var offset = index * page_size;
            var range_begin = index;
            var range_end = range_begin + page_size - 1;
            var range = range_begin + '-' + range_end;
            var entry = _.template('<li><a href="" range="<%= range %>"><%= range %></a></li>')({range: range});
            $(self).append(entry);
        });
    });

    // pager: make links from pagination entries
    $('.pagination a').click(function() {
        var action = $(this).attr('action');
        var range = $(this).attr('range');
        opsChooserApp.perform_search({range: range});
        return false;
    });

    // pager: mark proper pagination entry as active
    $('.pagination').find('a').each(function(i, anchor) {
        var anchor_range = $(anchor).attr('range');
        if (anchor_range == opsChooserApp.metadata.get('result_range')) {
            var li = $(anchor).parent();
            li.addClass('active');
        }
    });

    // metadata area: shorten cql query string
    $(".cql-query").shorten({showChars: 125, moreText: 'more', lessText: 'less'});

    // handle checkbox clicks by add-/remove-operations on basket
    $(".chk-patent-number").click(function() {
        var patent_number = this.value;
        if (this.checked)
            opsChooserApp.basketModel.add(patent_number);
        if (!this.checked)
            opsChooserApp.basketModel.remove(patent_number);
    });

    // handle button clicks by add-/remove-operations on basket
    $(".add-patent-number").click(function() {
        var patent_number = $(this).data('patent-number');
        opsChooserApp.basketModel.add(patent_number);
    });
    $(".remove-patent-number").click(function() {
        var patent_number = $(this).data('patent-number');
        opsChooserApp.basketModel.remove(patent_number);
    });

    // use jquery.shorten on "abstract" text
    $(".abstract").shorten({showChars: 2000, moreText: 'more', lessText: 'less'});

    // popovers
    $('.add-patent-number').popover();
    $('.remove-patent-number').popover();
    $('.btn-popover').popover();
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
    $(".query-link").click(function(event) {
        event.preventDefault();
        var attr = $(this).data('query-attribute');
        var val = $(this).data('query-value');
        var query = attr + '=' + val;
        opsChooserApp.send_query(query);
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
        var page = $(carousel).data('carousel').getActiveIndex() + 1;
        container.find('.drawing-number').text(page);

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
                console.warn('Error while fetching total count of drawings: ' + error);
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

}

function boot_application() {

    // hide pager- and metadata area at first
    $('.pager-area').hide();
    $('#pagination-info').hide();


    // application action: perform search
    $('.btn-query-perform').click(function() {
        opsChooserApp.perform_search();
    });

    // apply popovers to all desired buttons
    $('.btn-popover').popover();

    // auto-shorten some texts
    $(".very-short").shorten({showChars: 5, moreText: 'more', lessText: 'less'});


    // ------------------------------------------
    //   cql query area
    // ------------------------------------------

    // set cursor to end of query string, also focuses element
    $('#query').caret($('#query').val().length);

    // submit on meta+enter
    $('#query').on('keydown', null, 'meta+return', function() {
        opsChooserApp.perform_search();
    });

    // intercept and reformat clipboard content
    $("#query").on("paste", function(e) {

        // only run interceptor if content of target element is empty
        if ($(this).val()) return;

        e.preventDefault();

        var text = (e.originalEvent || e).clipboardData.getData('text');

        // show dialog to request modifier kind from
        $('#clipboard-modifier-chooser').modal('show');

        // modifier kind selected in dialog, compute and set new clipboard content
        $('.btn-clipboard-modifier').click(function() {

            // get field name and operator from dialog
            var modifier = $(this).data('modifier');
            var operator = $('#clipboard-modifier-operator').find('.btn.active').data('value') || 'OR';

            // close dialog
            $('#clipboard-modifier-chooser').modal('hide');

            // compute new clipboard content
            var query = _(text.split('\n')).map(function(item) {
                return modifier + '=' + item;
            }).join(' ' + operator + ' ');

            // set clipboard content and focus element
            $('#query').val(query);
            $('#query').focus();

        });

    });

    // trash icon clears the whole content
    $('#btn-query-clear').click(function() {
        $('#query').val('').focus();
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
            if (_.string.include(fiveleftchar, 'and') || _.string.include(fiveleftchar, 'or')) {
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
    $('#cql-field-chooser').select2({
        data: { results: OPS_CQL_FIELDS },
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
