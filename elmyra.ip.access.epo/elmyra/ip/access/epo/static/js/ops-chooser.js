// -*- coding: utf-8 -*-

/**
 * ------------------------------------------
 *            generic utilities
 * ------------------------------------------
 */

function to_list(value) {
    return _.isArray(value) && value || [value];
}


/**
 * ------------------------------------------
 *            application objects
 * ------------------------------------------
 */
OpsChooserApp = Backbone.Marionette.Application.extend({

    // send to server and process response
    perform_search: function(options) {
        var query = $('#query').val();
        if (!_.isEmpty(query)) {
            if (options && options.range) {
                opsChooserApp.search.perform(this.documents, this.metadata, query, options.range);
            } else {
                opsChooserApp.search.perform(this.documents, this.metadata, query);
            }
        }
    },

    send_query: function(query, options) {
        if (query) {
            $('#query').val(query);
            opsChooserApp.perform_search(options);
        }
    }

});
opsChooserApp = new OpsChooserApp();

opsChooserApp.addRegions({
    listRegion: "#ops-collection-region",
    paginationRegion: "#ops-pagination-region",
});



/**
 * ------------------------------------------
 *               model objects
 * ------------------------------------------
 */
OpsPublishedDataSearch = Backbone.Model.extend({
    url: '/api/ops/published-data/search',
    perform: function(documents, metadata, query, range) {

        documents.reset();
        $('#spinner').show();
        var self = this;

        this.fetch({
            data: $.param({ query: query, range: range}),
            success: function (payload) {

                $('#spinner').hide();
                $('#alert-area').empty();

                //console.log("payload raw:");
                //console.log(payload);
                console.log("payload data:");
                console.log(payload['attributes']);

                // get "node" containing record list from nested json response
                var search_result = payload['attributes']['ops:world-patent-data']['ops:biblio-search']['ops:search-result'];

                // unwrap response by creating a list of model objects from records
                var entries;
                if (search_result) {
                    var exchange_documents = to_list(search_result['exchange-documents']);
                    entries = _.map(exchange_documents, function(entry) { return new OpsExchangeDocument(entry['exchange-document']); });
                }

                // propagate data to model collection instance
                documents.reset(entries);

                // propagate metadata to model
                var total_result_count = payload['attributes']['ops:world-patent-data']['ops:biblio-search']['@total-result-count'];
                metadata.set({result_count: total_result_count});

                // run action bindings here after rendering data entries
                listview_bind_actions();

            },
            error: function(e, xhr) {

                //console.log("error: " + xhr.responseText);

                $('#spinner').hide();
                $('#alert-area').empty();
                documents.reset();

                response = jQuery.parseJSON(xhr.responseText);
                if (response['status'] == 'error') {
                    _.each(response['errors'], function(error) {
                        var tpl = _.template($('#backend-error-template').html());
                        var alert_html = tpl(error);
                        $('#alert-area').append(alert_html);
                    });
                    $(".very-short").shorten({showChars: 0, moreText: 'more', lessText: 'less'});
                }
            }
        });

    },
});

OpsExchangeMetadata = Backbone.Model.extend({

    defaults: {
        result_count: null,
    }

});

OpsExchangeDocument = Backbone.Model.extend({

    defaults: {
        selected: false,

        // TODO: move these methods to "viewHelpers"
        // http://lostechies.com/derickbailey/2012/04/26/view-helpers-for-underscore-templates/
        // https://github.com/marionettejs/backbone.marionette/wiki/View-helpers-for-underscore-templates#using-this-with-backbonemarionette

        get_patent_number: function() {
            return this['@country'] + this['@doc-number'] + this['@kind'];
        },

        get_application_number: function(source) {
            var application_references = this['bibliographic-data']['application-reference']['document-id'];
            for (i in application_references) {
                var item = application_references[i];
                if (source == 'docdb' && item['@document-id-type'] == 'docdb') {
                    return item['country']['$'] + item['doc-number']['$'];
                } else if (source == 'original' && item['@document-id-type'] == 'original') {
                    return item['doc-number']['$'];
                }
            }
        },

        get_applicants: function(links) {
            try {
                var applicants_root_node = this['bibliographic-data']['parties']['applicants'];
                applicants_root_node = applicants_root_node || [];
                var applicants_node = applicants_root_node['applicant'];
                var applicants_list = this.parties_to_list(applicants_node, 'applicant-name');
                if (links) {
                    applicants_list = this.enrich_links(applicants_list, 'applicant');
                }
                return applicants_list;

            } catch(e) {
                console.warn('patent-search: applicants could not be parsed from document ' + this.get_patent_number());
                return [];
            }
        },

        get_inventors: function(links) {
            try {
                var inventors_root_node = this['bibliographic-data']['parties']['inventors'];
                inventors_root_node = inventors_root_node || [];
                var inventors_node = inventors_root_node['inventor'];
                var inventor_list = this.parties_to_list(inventors_node, 'inventor-name');
                if (links) {
                    inventor_list = this.enrich_links(inventor_list, 'inventor');
                }
                return inventor_list;

            } catch(e) {
                console.warn('patent-search: inventors could not be parsed from document ' + this.get_patent_number());
                return [];
            }
        },

        parties_to_list: function(container, value_attribute_name) {

            // deserialize list of parties (applicants/inventors) from exchange payload
            var sequence_max = "0";
            var groups = {};
            _.each(container, function(item) {
                var data_format = item['@data-format'];
                var sequence = item['@sequence'];
                var value = _.string.trim(item[value_attribute_name]['name']['$'], ', ');
                groups[data_format] = groups[data_format] || {};
                groups[data_format][sequence] = value;
                if (sequence > sequence_max)
                    sequence_max = sequence;
            });
            //console.log(groups);

            // TODO: somehow display in gui which one is the "epodoc" and which one is the "original" value
            var entries = [];
            _.each(_.range(1, parseInt(sequence_max) + 1), function(sequence) {
                sequence = sequence.toString();
                var epodoc_value = groups['epodoc'][sequence];
                var original_value = groups['original'][sequence];
                //entries.push(epodoc_value + ' / ' + original_value);
                entries.push(original_value);
            });

            return entries;

        },

        get_ipc_list: function(links) {
            var ipc_list = [];
            var ipc_node_top = this['bibliographic-data']['classifications-ipcr'];
            if (ipc_node_top) {
                var ipc_node = to_list(ipc_node_top['classification-ipcr']);
                ipc_list = _.map(ipc_node, function(ipc) {
                    return ipc['text']['$'];
                });
            }

            if (links) {
                ipc_list = this.enrich_links(ipc_list, 'ipc', function(value) {
                    return value.substring(0, 15).replace(/ /g, '')
                });
            }
            return ipc_list;

        },

        enrich_links: function(container, attribute, value_modifier) {
            var self = this;
            return _.map(container, function(item) {
                return self.enrich_link(item, attribute, value_modifier);
            });
        },

        enrich_link: function(item, attribute, value_modifier) {
            var label = item;
            var value = item;
            if (value_modifier)
                value = value_modifier(value);
            var link_tpl = _.template('<a class="query-link" href="" data-query-attribute="<%= attribute %>" data-query-value="<%= value %>"><%= label %></a>');
            var link = link_tpl({attribute: attribute, value: value, label: label});
            return link;
        },

        get_drawing_url: function() {
            // http://ops.epo.org/3.1/rest-services/published-data/images/EP/1000000/PA/firstpage.png?Range=1
            // http://ops.epo.org/3.1/rest-services/published-data/images/US/20130311929/A1/thumbnail.tiff?Range=1
            var url_tpl = _.template('/api/ops/<%= patent_number %>/image/drawing');
            var url = url_tpl({patent_number: this.get_patent_number()});
            return url;
        },

        get_fullimage_url: function() {
            // http://ops.epo.org/3.1/rest-services/published-data/images/EP/1000000/A1/fullimage.pdf?Range=1
            var url_tpl = _.template('/api/ops/<%= patent_number %>/image/full');
            var url = url_tpl({patent_number: this.get_patent_number()});
            return url;
        },

        get_espacenet_pdf_url: function() {
            // http://worldwide.espacenet.com/espacenetDocument.pdf?flavour=trueFull&FT=D&CC=US&NR=6269530B1&KC=B1
            var url_tpl = _.template('http://worldwide.espacenet.com/espacenetDocument.pdf?flavour=trueFull&FT=D&CC=<%= country %>&NR=<%= docnumber %><%= kind %>&KC=<%= kind %>');
            var url = url_tpl({country: this['@country'], docnumber: this['@doc-number'], kind: this['@kind']});
            return url;
        },

        get_ops_pdf_url: function() {
            // /api/ops/EP0666666B1/pdf/all
            var url_tpl = _.template('/api/ops/<%= country %><%= docnumber %><%= kind %>/pdf/all');
            var url = url_tpl({country: this['@country'], docnumber: this['@doc-number'], kind: this['@kind']});
            return url;
        },

        get_epo_register_url: function() {
            // https://register.epo.org/application?number=EP95480005
            var url_tpl = _.template('https://register.epo.org/application?number=<%= application_number %>');
            var url = url_tpl({application_number: this.get_application_number('docdb')});
            return url;
        },

        get_inpadoc_legal_url: function() {
            // http://worldwide.espacenet.com/publicationDetails/inpadoc?CC=US&NR=6269530B1&KC=B1&FT=D
            var url_tpl = _.template('http://worldwide.espacenet.com/publicationDetails/inpadoc?FT=D&CC=<%= country %>&NR=<%= docnumber %><%= kind %>&KC=<%= kind %>');
            var url = url_tpl({country: this['@country'], docnumber: this['@doc-number'], kind: this['@kind']});
            return url;
        },

        get_dpma_register_url: function() {

            // DE19630877.1 / DE19630877A1 / DE000019630877C2
            // http://localhost:6543/ops/browser?query=pn=DE19630877A1
            // http://localhost:6543/jump/dpma/register?pn=DE19630877
            // https://register.dpma.de/DPMAregister/pat/register?AKZ=196308771

            // DE102012009645.3 / DE102012009645A1
            // http://localhost:6543/ops/browser?query=pn=DE102012009645
            // http://localhost:6543/jump/dpma/register?pn=DE102012009645
            // https://register.dpma.de/DPMAregister/pat/register?AKZ=1020120096453

            var url_tpl = _.template('/jump/dpma/register?pn=<%= application_number %>');
            var url = url_tpl({application_number: this.get_application_number('docdb')});
            return url;
        },

        get_uspto_pair_url: function() {
            // http://portal.uspto.gov/pair/PublicPair
            var url_tpl = _.template('http://portal.uspto.gov/pair/PublicPair');
            var url = url_tpl({country: this['@country'], docnumber: this['@doc-number'], kind: this['@kind']});
            return url;
        },

    },

    select: function() {
        this.set('selected', true);
    },
    unselect: function() {
        this.set('selected', false);
    },


});

OpsExchangeDocumentCollection = Backbone.Collection.extend({

    model: OpsExchangeDocument,

    initialize: function(collection) {
        var self = this;
    },

});



/**
 * ------------------------------------------
 *                view objects
 * ------------------------------------------
 */
OpsExchangeDocumentView = Backbone.Marionette.ItemView.extend({
    //template: "#ops-entry-template",
    template: _.template($('#ops-entry-template').html(), this.model, {variable: 'data'}),
    tagName: 'div',
    className: 'row-fluid',

    events: {
        'click .rank_up img': 'rankUp',
        'click .rank_down img': 'rankDown',
        'click a.disqualify': 'disqualify'
    },

    // actions to run after populating the view
    // e.g. to bind click handlers on individual records
    onDomRefresh: function() {

        var patent_number = this.model.attributes.get_patent_number();
        basket_update_ui_entry(patent_number);

    },

});

OpsExchangeDocumentCollectionView = Backbone.Marionette.CompositeView.extend({
    tagName: "div",
    id: "opsexchangedocumentcollection",
    className: "container",
    template: "#ops-collection-template",
    itemView: OpsExchangeDocumentView,

    appendHtml: function(collectionView, itemView) {
        $(collectionView.el).append(itemView.el);
    },

});

PaginationView = Backbone.Marionette.ItemView.extend({
    tagName: "div",
    id: "paginationview",
    template: "#ops-pagination-template",

    initialize: function() {
        console.log('PaginationView.initialize');
        this.listenTo(this.model, "change", this.render);
    },

    onDomRefresh: function() {
        console.log('PaginationView.onDomRefresh');
        $('div.pagination a').click(function() {
            var action = $(this).attr('action');
            var range = $(this).attr('range');
            opsChooserApp.perform_search({range: range});
            return false;
        });
    },

});


/*
------------------------------------------
    utility functions
------------------------------------------
 */

function basket_add(entry) {
    var payload = $('#basket').val();
    if (!_.string.include(payload, entry))
        if (payload != '' && !_.string.endsWith(payload, '\n'))
            payload += '\n'
        payload += entry + '\n';
    $('#basket').val(payload);
    basket_update_ui_entry(entry);
}

function basket_remove(entry) {
    var payload = $('#basket').val();
    if (_.string.include(payload, entry))
        payload = payload.replace(entry + '\n', '');
    $('#basket').val(payload);
    basket_update_ui_entry(entry);
}

function basket_update_ui_entry(entry) {
    // backpropagate current basket entries into checkbox state
    //console.log(this.model);
    var payload = $('#basket').val();
    var checkbox_element = $('#' + 'chk-patent-number-' + entry);
    var add_button_element = $('#' + 'add-patent-number-' + entry);
    var remove_button_element = $('#' + 'remove-patent-number-' + entry);
    if (_.string.include(payload, entry)) {
        checkbox_element && checkbox_element.prop('checked', true);
        add_button_element && add_button_element.hide();
        remove_button_element && remove_button_element.show();
    } else {
        checkbox_element && checkbox_element.prop('checked', false);
        add_button_element && add_button_element.show();
        remove_button_element && remove_button_element.hide();
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

    // handle checkbox clicks by add-/remove-operations on basket
    $(".chk-patent-number").click(function() {
        var patent_number = this.value;
        if (this.checked)
            basket_add(patent_number);
        if (!this.checked)
            basket_remove(patent_number);
    });

    // handle button clicks by add-/remove-operations on basket
    $(".add-patent-number").click(function() {
        var patent_number = $(this).data('patent-number');
        basket_add(patent_number);
    });
    $(".remove-patent-number").click(function() {
        var patent_number = $(this).data('patent-number');
        basket_remove(patent_number);
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
        var query = attr + '=' + '"' + val + '"';
        opsChooserApp.send_query(query);
        $(window).scrollTop(0);
    });

    // make the carousel fly

    // turn slideshow off
    $('.drawings-carousel').carousel({
        interval: null
    });

    // show page number
    $('.drawings-carousel').bind('slid', function(event) {
        var page = $(this).data('carousel').getActiveIndex() + 1;
        $(this).closest('.ops-collection-entry').find('.page-number').text('Drawing: ' + page);
    });

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
        // inquire it from image information metadata and cache associated with dom element
        var max_count = carousel_items.data('max_count');

        if (!max_count) {
            max_count = 1;
            var document_number = carousel.closest('.ops-collection-entry').data('document-number');
            if (!document_number) {
                console.warn("document-number could not be found, won't proceed loading items into carousel");
                return;
            }
            //console.log(document_number);
            var image_info_url = _.template('/api/ops/<%= patent %>/image/info')({ patent: document_number });
            //console.log(image_info_url);

            $.ajax({url: image_info_url, async: false}).success(function(payload) {
                max_count = payload['META']['drawing-total-count'];
                console.log('Found drawing count: ' + max_count);
            }).error(function(error) {
                console.log('Error while fetching drawing count: ' + error);
            });
            carousel_items.data('max_count', max_count);
        }

        // skip if max_count is invalid
        if (!max_count) return;

        // skip if all drawings are already established
        if (item_count >= max_count) return;


        // build a new carousel item from the last one
        var blueprint = $(carousel_items).children(':first').clone();
        $(blueprint).removeClass('active');

        // manipulate nested img src: bump page number
        var img = $(blueprint).children('img');
        var src = img.attr('src').replace(/\?page=.*/, '');
        src += '?page=' + (item_index + 1);
        img.attr('src', src);

        //console.log(src);

        // add carousel item
        $(carousel_items).append(blueprint);

    });


    // hide broken drawing images
    var images = $('.drawings-carousel').find('img');
    images.error(function() {
        $(this).hide();
        $(this).closest('.carousel').hide().parent().append('<br/><br/><br/><br/><p align="center">No image</p>');
    }); //.attr("src", "missing.png");

}


/**
 * ------------------------------------------
 *           bootstrap application
 * ------------------------------------------
 */

opsChooserApp.addInitializer(function(options) {
    // create application domain model objects
    this.search = new OpsPublishedDataSearch();
    this.metadata = new OpsExchangeMetadata();
    this.documents = new OpsExchangeDocumentCollection();
});

opsChooserApp.addInitializer(function(options) {

    // bind model objects to view objects
    var collectionView = new OpsExchangeDocumentCollectionView({
        collection: this.documents
    });
    var paginationView = new PaginationView({
        model: this.metadata
    });

    // bind view objects to region objects
    opsChooserApp.listRegion.show(collectionView);
    opsChooserApp.paginationRegion.show(paginationView);
});

opsChooserApp.addInitializer(function(options) {
    // automatically run search after bootstrapping application
    this.perform_search();
});

$(document).ready(function() {

    console.log("OpsChooserApp starting");

    // process and propagate application ingress parameters
    //var url = $.url(window.location.href);
    //var query = url.param('query');
    //query = 'applicant=IBM';
    //query = 'publicationnumber=US2013255753A1';

    opsChooserApp.start();

    $('#query-button').click(function() {
        opsChooserApp.perform_search();
    });

    $('#basket-review-button').click(function() {
        // compute cql query from numberlist in basket
        var basket = $('#basket').val();
        var query = basket
            .split('\n')
            .filter(function(entry) { return entry; })
            .map(function(entry) { return 'pn=' + entry; }).join(' OR ');
        if (query) {
            $('#query').val(query);
            opsChooserApp.perform_search();
        }
    });

    $('.btn-popover').popover();

    $(".very-short").shorten({showChars: 5, moreText: 'more', lessText: 'less'});

});
