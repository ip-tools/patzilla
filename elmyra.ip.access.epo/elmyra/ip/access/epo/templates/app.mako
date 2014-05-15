## -*- coding: utf-8 -*-

<%inherit file="site.mako" />

<%block name="body">

## http://bootsnipp.com/snipps/e-mail-interface-like-gmail
## http://davidsulc.com/blog/2012/04/15/a-simple-backbone-marionette-tutorial/
## https://github.com/davidsulc/backbone.marionette-collection-example

<%
query = request.params.get('query', '')
html_title = request.params.get('html-title', 'Patent search for "{0}"'.format(query))
page_title = request.params.get('page-title', 'Patent search')
page_subtitle = request.params.get('page-subtitle', '')
page_footer = request.params.get('page-footer', 'Data sources: EPO/OPS, DPMA/DEPATISnet, USPTO/PATIMG')
app_productname = request.params.get('app-productname', 'elmyra <i class="circle-icon">IP</i> suite')
app_versionstring = request.params.get('app-versionstring', '<br/>Software release: ' + request.registry.settings.get('SOFTWARE_VERSION', ''))
ship_mode = request.params.get('ship-mode', 'multi-numberlist')
ship_url = request.params.get('ship-url', request.params.get('ship_url', ''))
ship_frame = request.params.get('ship-frame', 'opsbrowser_right_frame')
embed_item_url = request.params.get('embed-item-url', '')
%>
<script type="application/javascript">
var ship_mode = decodeURIComponent('${ship_mode}');
var ship_url = decodeURIComponent('${ship_url}');
var ship_frame = decodeURIComponent('${ship_frame}');
var embed_item_url = decodeURIComponent('${embed_item_url}');
var PRINTMODE = '${printmode}' == 'True' ? true : false;
</script>

## title / headline
<div class="container-fluid">
    <div class="span8">
        <div class="pull-left">
        <h3 style="display: inline-block">${page_title | n}</h3>
        &nbsp;&nbsp;&nbsp;
        ${page_subtitle}
        </div>
    </div>
    <div class="span4">
        <div class="pull-right">
            <h3>${app_productname | n}</h3>
        </div>
    </div>
</div>

<div class="container-fluid span12">

    ## query builder and basket
    <div class="row-fluid do-not-print" id="querybuilder-basket-area">

        <div class="span8" id="querybuilder-area">

            <div class="row-fluid">
                <div class="span8">
                    <h6 style="display: inline">
                        <a href="https://en.wikipedia.org/wiki/Contextual_Query_Language" target="_blank">About CQL</a>
                    </h6>
                </div>
                <div class="span3">
                    <div id="datasource" class="btn-group pull-right" data-toggle="buttons-radio">
                      <button class="btn active" data-value="ops">OPS</button>
                      <button class="btn" data-value="depatisnet">DEPATISnet</button>
                    </div>
                </div>
                <div class="span1">
                    <a id="btn-query-clear" class="icon-trash icon-large"></a>
                </div>
            </div>

            <div class="row-fluid">

                <div class="span11">
                    <textarea class="span12" id="query" name="query" placeholder="CQL expression" rows="5">${query}</textarea>
                </div>

                <div class="span1">

                    <!--
                    <div id="cql-quick-operator" class="btn-group" data-toggle="buttons-radio">
                        <button class="btn-cql-boolean btn btn-mini active" type="button" data-value="OR">OR</button>
                        <button class="btn-cql-boolean btn btn-mini"        type="button" data-value="AND">AND</button>
                    </div>

                    <a class="btn-cql-field label label-success" data-value="num=">num=</a>
                    <a class="btn-cql-field label label-info" data-value="txt=">txt=</a>
                    <a class="btn-cql-field label label-important" data-value="cl=">cl=</a>
                    -->

                </div>

            </div>

            <div class="row-fluid">

                <div class="span4">

                    <div class="btn-group btn-popover"
                        data-toggle="popover" data-trigger="hover" data-placement="right"
                        data-content="Send query to database"
                        >
                        <button type="submit" role="button" class="btn btn-query-perform">
                            <i class="icon-star" id="idler"></i>
                            <i class="icon-refresh icon-spin" style="display: none" id="spinner"></i>
                        </button>
                        <button type="submit" role="button" class="btn btn-query-perform">
                            Send query
                        </button>
                    </div>

                </div>

                <div class="span7">
                    <div id="cql-field-chooser" name="cql-field-chooser" size="1"></div>
                </div>

                <div class="span1">
                </div>

            </div>

        </div>

        % if ship_mode != 'single-bibdata':
        <div class="span4" id="basket-area"></div>
        % endif

    </div>


    ## pager top
    <div class="pager-area do-not-print" id="ops-pagination-region-top"></div>

    ## notifications and alerts
    <div id="alert-area"></div>
    <div id="info-area"></div>

    ## results
    <div id="ops-metadata-region"></div>
    <div id="ops-collection-region"></div>

    ## pager bottom
    <div class="pager-area do-not-print" id="ops-pagination-region-bottom"></div>

    <hr class="clear-margin" style="margin-top: 50px"/>
    <div class="page-footer pull-left">
        &copy; 2013-2014, Elmyra UG — All rights reserved.
    </div>
    <div class="page-footer pull-right">
        <small>
            <div style="text-align: right">
                ${page_footer | n}${app_versionstring | n}
            </div>
        </small>
    </div>

</div>


<!-- modal dialog for viewing pdf -->
<div id="ops-pdf-modal" class="modal hide fade" tabindex="-1" role="dialog" aria-labelledby="ops-pdf-modal-label" aria-hidden="true">
    <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-hidden="true">×</button>
        <h3 id="ops-pdf-modal-label"></h3>
    </div>
    <div class="modal-body" id="pdf">
    </div>
    <div class="modal-footer">
        <div class="btn-group pull-left">
            <button class="btn btn-primary" id="pdf-previous">Previous</button>
            <button class="btn btn-primary" id="pdf-next">Next</button>
        </div>
        <button class="btn" data-dismiss="modal" aria-hidden="true">Close</button>
    </div>
</div>


<!-- modal dialog for choosing clipboard content modifier -->
<div id="clipboard-modifier-chooser" class="modal hide fade" tabindex="-1" role="dialog" aria-labelledby="clipboard-modifier-chooser-label" aria-hidden="true">
    <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-hidden="true">×</button>
        <h3 id="clipboard-modifier-chooser-label">Choose clipboard transformation...</h3>
    </div>
    <div class="modal-body">
        <div class="btn-group btn-group-vertical">
            <button class="btn btn-large btn-success btn-clipboard-modifier" data-modifier="num">
                <strong>Publication-, application- or priority number</strong>
                <br/><br/>
                <small>FIXME: examples</small>
            </button>
            <button class="btn btn-large btn-info btn-clipboard-modifier" data-modifier="txt">
                <strong>Title, abstract, inventor-, or applicant name</strong>
                <br/><br/>
                <small>FIXME: examples</small>
            </button>
            <button class="btn btn-large btn-danger btn-clipboard-modifier" data-modifier="cl">
                <strong>CPC or IPC8 class</strong>
                <br/><br/>
                <small>FIXME: examples</small>
            </button>
        </div>
    </div>
    <div class="modal-footer">
        <div id="clipboard-modifier-operator" class="btn-group pull-left" data-toggle="buttons-radio">
            <button class="btn active" type="button" data-value="OR">OR</button>
            <button class="btn"        type="button" data-value="AND">AND</button>
        </div>
        <button class="btn" data-dismiss="modal" aria-hidden="true">Close</button>
    </div>
</div>


## ------------------------------------------
##   pager template
## ------------------------------------------
<%text>
<script type="text/x-underscore-template" id="ops-pagination-template">
    <div id="pagination-widget">

        <div class="row-fluid" id="pagination-chooser">

            <!-- legal status -->
            <div class="span2">
                <div class="btn-group btn-popover page-size-chooser"
                            data-toggle="popover" data-trigger="hover" data-placement="right"
                            data-content="Select page size"
                    >
                    <button class="btn dropdown-toggle" data-toggle="dropdown">
                        <i class="icon-resize-vertical"></i> &nbsp; Page size
                    </button>
                    <button class="btn dropdown-toggle" data-toggle="dropdown">
                        <span class="caret"></span>
                    </button>
                    <ul class="dropdown-menu">
                    </ul>
                </div>
            </div>

            <div class="span10 pagination">
                <ul class="pull-right">
                    <!--
                    <li><a href="#" action="previous">Prev</a></li>
                    -->
                    <!--
                    <li><a href="#" action="next">Next</a></li>
                    -->
                </ul>
            </div>
        </div>

    </div>
</script>
</%text>


## ------------------------------------------
##   metadata template
## ------------------------------------------
<%text>
<script type="text/x-underscore-template" id="ops-metadata-template">
    <!--
    <div class="row-fluid" id="pagination-info">
        <div class="span12 pagination-centered">

            &nbsp;&nbsp;
            current = <span class="badge badge-info"><%= result_range %></span>
        </div>
    </div>
    -->

    <div class="row-fluid container-fluid ops-collection-entry" id="pagination-info">

        <div class="ops-collection-entry-heading row-fluid">

            <!-- total result count -->
            <div class="span1">
                Total:
                <br/>
                <span style="font-size: x-large"><%= result_count | 0 %></span>
            </div>

            <!-- current display range -->
            <div class="span2">
                Range:
                <br/>
                <span style="font-size: x-large"><%= result_range %></span>
            </div>

            <!-- current cql query string -->
            <div class="span7">
                Query:
                <br/>
                <span style="font-size: small" class="cql-query"><%= query_real %></span>
            </div>

            <div class="span2">

                <!-- result actions -->
                <div class="btn-group btn-popover span7 result-actions do-not-print"
                            data-toggle="popover" data-trigger="hover" data-placement="left"
                            data-content="Export results"
                    >
                    <button class="btn dropdown-toggle" data-toggle="dropdown">
                        <i class="icon-download-alt icon-large2"></i> &nbsp; Export
                    </button>
                    <button class="btn dropdown-toggle" data-toggle="dropdown">
                        <span class="caret"></span>
                    </button>
                    <ul class="dropdown-menu">

                        <!-- bibliographic data -->
                        <li>
                            <a href="<%= get_url_pdf() %>" target="_blank">
                                <img src="/static/img/icons/pdf.svg" width="16" height="16"/> PDF
                            </a>
                            <a href="<%= get_url_print() %>" target="_blank">
                                <i class="icon-print icon-large"></i> Print
                            </a>
                        </li>
                    </ul>
                </div>

            </div>

        </div>
    </div>

</script>
</%text>


## ------------------------------------------
##   result list template
## ------------------------------------------
<script id="ops-collection-template" type="text/x-underscore-template">
    <!--
    <div id="ops-collection-entry" class="row"/>
    -->
</script>



## ------------------------------------------
##   result item template
## ------------------------------------------
<script id="ops-entry-template" type="text/x-underscore-template">

        <%text>
        <%

        // 1. log model item to assist in data exploration
        console.log(data);


        // 2.1 utility functions

        // date values inside publication|application-reference
        function search_date(node) {
            var value = null;
            _.each(node, function(item) {
                if (!value && item['date'] && item['date']['$']) {
                    value = item['date']['$'];
                }
            });
            return value;
        }

        function format_date(value) {
            if (value) {
                return value.slice(0, 4) + '-' + value.slice(4, 6) + '-' + value.slice(6, 8);
            }
        }


        // 2.2 prepare some template variables

        var patent_number = data.get_patent_number();
        var drawing_url = data.get_drawing_url();
        var fullimage_url = data.get_fullimage_url();
        var espacenet_pdf_url = data.get_espacenet_pdf_url();
        var ops_pdf_url = data.get_ops_pdf_url();
        var epo_register_url = data.get_epo_register_url();
        var inpadoc_legal_url = data.get_inpadoc_legal_url();
        var dpma_register_url = data.get_dpma_register_url();
        var uspto_pair_url = data.get_uspto_pair_url();
        var inpadoc_family_url = data.get_inpadoc_family_url();
        var ops_family_url = data.get_ops_family_url();
        var ccd_viewer_url = data.get_ccd_viewer_url();
        var depatisnet_url = data.get_depatisnet_url();

        var publication_date = format_date(search_date(data['bibliographic-data']['publication-reference']['document-id']));
        var application_date = format_date(search_date(data['bibliographic-data']['application-reference']['document-id']));

        // title
        var title_list = [];
        var title_node = data['bibliographic-data']['invention-title'];
        if (title_node) {
            title_list = _.map(to_list(title_node), function(title) {
                var lang_prefix = title['@lang'] && '[' + title['@lang'].toUpperCase() + '] ' || '';
                return lang_prefix + title['$'];
            });
        }

        var abstract_list = [];
        if (data['abstract']) {
            var abstract_node = to_list(data['abstract']);
            var abstract_list = abstract_node.map(function(node) {
                var text_nodelist = to_list(node['p']);
                var text = text_nodelist.map(function(node) { return node['$']; }).join(' ');
                var lang_prefix = node['@lang'] && '[' + node['@lang'].toUpperCase() + '] ' || '';
                return lang_prefix + text;
            });
        }

        %>
        </%text>


        <%text>
        <div class="container-fluid ops-collection-entry" data-document-number="<%= patent_number %>" style="page-break-after: always;">

            <div class="ops-collection-entry-heading row-fluid">

                <!-- patent number -->
                <div class="span3">
                    <h3 class="header-compact">
                        <%= data.enrich_link(patent_number, 'pn') %>
                    </h3>
                </div>

                <!-- dates -->
                <div class="span4 container-fluid">
                    <div class="span6">
                        <dl class="dl-horizontal dl-horizontal-biblio">
                            <dt class="inid-tooltip" data-toggle="tooltip" title="application date">
                                (22)
                            </dt>
                            <dd>
                                <%= application_date %>
                            </dd>
                        </dl>
                    </div>
                    <div class="span6">
                        <dl class="dl-horizontal dl-horizontal-biblio">
                            <dt class="inid-tooltip" data-toggle="tooltip" title="publication date">
                                (45)
                            </dt>
                            <dd>
                                <%= data.enrich_link(publication_date, 'publicationdate') %>
                            </dd>
                        </dl>
                    </div>
                </div>

                <!-- actions -->
                <div class="span5 container-fluid pull-right document-actions do-not-print">
                    <div class="span8">


                        <!-- pdf document -->
                        <div class="btn-group btn-popover span5"
                                    data-toggle="popover" data-trigger="hover" data-placement="top"
                                    data-content="Download full pdf documents from various sources"
                            >
                            <button class="btn dropdown-toggle" data-toggle="dropdown">
                                <img src="/static/img/icons/pdf.svg" width="16" height="16"/>
                                PDF
                            </button>
                            <button class="btn dropdown-toggle" data-toggle="dropdown">
                                <span class="caret"></span>
                            </button>
                            <ul class="dropdown-menu">
                                <li>
                                    <a href="<%= ops_pdf_url %>" target="_blank">
                                        [PDF] <%= patent_number %> @ OPS
                                    </a>
                                </li>
                                <li>
                                    <a href="<%= espacenet_pdf_url %>" target="_blank">
                                        [PDF] <%= patent_number %> @ Espacenet
                                    </a>
                                </li>
                            </ul>
                        </div>



                        <!-- external links -->
                        <div class="btn-group btn-popover span7"
                                    data-toggle="popover" data-trigger="hover" data-placement="top"
                                    data-content="Show more information from various patent offices"
                            >
                            <button class="btn dropdown-toggle" data-toggle="dropdown">
                                <i class="icon-globe icon-large"></i> More
                            </button>
                            <button class="btn dropdown-toggle" data-toggle="dropdown">
                                <span class="caret"></span>
                            </button>
                            <ul class="dropdown-menu">

                                <!-- bibliographic data -->
                                <li><div style="padding-left: 10px">
                                    <h5><i class="icon-list"></i> &nbsp; Bibliographic data</h5>
                                    </div>
                                </li>
                                <li>
                                    <a href="<%= depatisnet_url %>" target="_blank">
                                        [BIBLIO] <%= patent_number %> @ DEPATISnet
                                    </a>
                                </li>
                                <li class="divider"/>


                                <!-- legal status -->
                                <li><div style="padding-left: 10px">
                                    <h5>§ &nbsp; Legal information</h5>
                                    </div>
                                </li>
                                <li>
                                    <a href="<%= inpadoc_legal_url %>" target="_blank">
                                        [LEGAL] <%= patent_number %> @ INPADOC legal status
                                    </a>
                                </li>
                                <li>
                                    <a href="<%= epo_register_url %>" target="_blank">
                                        [LEGAL] <%= patent_number %> @ European Patent Register
                                    </a>
                                </li>
                                <li>
                                    <a href="<%= dpma_register_url %>" target="_blank">
                                        [LEGAL] <%= patent_number %> @ DPMAregister
                                    </a>
                                </li>
                                <li>
                                    <a href="<%= uspto_pair_url %>" target="_blank">
                                        [LEGAL] USPTO PAIR
                                    </a>
                                </li>
                                <li class="divider"/>


                                <!-- patent family -->
                                <li><div style="padding-left: 10px">
                                    <h5><i class="icon-group"></i> &nbsp; Patent family information</h5>
                                    </div>
                                </li>
                                <li>
                                    <a href="<%= ccd_viewer_url %>" target="_blank">
                                        [FAMILY] <%= patent_number %> @ CCD Viewer
                                    </a>
                                </li>
                                <li>
                                    <a href="<%= inpadoc_family_url %>" target="_blank">
                                        [FAMILY] <%= patent_number %> @ INPADOC patent family
                                    </a>
                                </li>
                                <li>
                                    <a href="<%= ops_family_url %>" target="_blank">
                                        [FAMILY] <%= patent_number %> @ OPS biblio,legal
                                    </a>
                                </li>

                            </ul>
                        </div>

                    </div>
                    <div class="span4">
                        </%text>

                        % if ship_mode == 'multi-numberlist':
                            <%text>
                            <input type="checkbox" id="chk-patent-number-<%= patent_number %>" class="chk-patent-number hide" value="<%= patent_number %>"/>
                            <a id="add-patent-number-<%= patent_number %>" role="button" class="btn add-patent-number"
                                data-patent-number="<%= patent_number %>"
                                data-toggle="popover" data-trigger="hover" data-placement="bottom" data-content="Add document number to basket"
                                >
                                <i class="icon-white icon-plus"></i> Add
                            </a>
                            <a id="remove-patent-number-<%= patent_number %>" role="button" class="btn remove-patent-number"
                                data-patent-number="<%= patent_number %>"
                                data-toggle="popover" data-trigger="hover" data-placement="bottom" data-content="Remove document number from basket"
                                >
                                <i class="icon-white icon-minus"></i> Remove
                            </a>
                            </%text>
                        % endif

                        % if ship_mode == 'single-bibdata':
                        <%text>
                            <form name="single-bibdata-<%= patent_number %>" method="post" action="<%= ship_url %>" target="<%= ship_frame %>">
                                <input name="query" type="hidden" value="<%= $('#query').val().replace(/"/g, '&quot;') %>"/>
                                <input name="patent_number" type="hidden" value="<%= patent_number %>"/>
                                <input name="title" type="hidden" value="<%= title_list.join('\n') %>"/>
                                <input name="applicants" type="hidden" value="<%= data.get_applicants().join('\n') %>"/>
                                <input name="inventors" type="hidden" value="<%= data.get_inventors().join('\n') %>"/>
                                <input name="application_date" type="hidden" value="<%= application_date %>"/>
                                <input name="publication_date" type="hidden" value="<%= publication_date %>"/>
                                <input name="ipcs" type="hidden" value="<%= data.get_ipc_list().join('\n') %>"/>
                                <input name="abstract" type="hidden" value="<%= abstract_list.join('\n') %>"/>
                                <!--
                                <input name="ship_action" type="submit" value="rate" class="btn"/>
                                -->
                                <button type="submit" role="button" class="btn btn-popover"
                                    data-toggle="popover" data-trigger="hover" data-placement="bottom"
                                    data-content="Submit details of document to origin or 3rd-party system"
                                    >
                                    <i class="icon-share"/>
                                    Submit
                                </button>

                            </form>
                        </%text>
                        % endif

                        <%text>
                    </div>
                </div>

            </div>

            <div class="ops-collection-entry-inner container-fluid">

                <div class="row-fluid">
                    <div class="span12 document_title">
                        <strong><%= title_list.join('<br/>') %></strong>
                    </div>
                </div>

                <div class="row-fluid">
                    <div class="span5">

                        <!-- first drawing only -->
                        <!--
                        <img src="<%= drawing_url %>" alt="No drawing available."/>
                        -->

                        <!-- carousel for all drawings -->
                        <div id="drawings-carousel-<%= patent_number %>" class="carousel slide drawings-carousel">
                            <!--
                            <ol class="carousel-indicators">
                                <li data-target="#drawings-carousel" data-slide-to="0" class="active"></li>
                                <li data-target="#drawings-carousel" data-slide-to="1"></li>
                                <li data-target="#drawings-carousel" data-slide-to="2"></li>
                            </ol>
                            -->
                            <!-- carousel items -->
                            <div class="carousel-inner">
                                <div class="active item">
                                    <img src="<%= drawing_url %>" alt="No drawing available."/>
                                </div>
                            </div>
                            <!-- carousel navigation -->
                            <a class="carousel-control left do-not-print" href="#drawings-carousel-<%= patent_number %>" data-slide="prev">&lsaquo;</a>
                            <a class="carousel-control right do-not-print" href="#drawings-carousel-<%= patent_number %>" data-slide="next">&rsaquo;</a>
                        </div>

                        <div class="drawing-info span12 text-center">
                            Drawing #<span class="drawing-number">1</span><span class="drawing-totalcount"/>
                        </div>

                    </div>
                    <div class="span7 document_details">

                        <dl class="dl-horizontal dl-horizontal-biblio">

                            <dt class="inid-tooltip" data-toggle="tooltip" title="applicants">
                                (71)
                            </dt>
                            <dd>
                                <%= data.get_applicants(true).map(function(item) { return '<strong>' + item + '</strong>'; }).join('<br/>') %>
                            </dd>

                            <dt class="inid-tooltip" data-toggle="tooltip" title="inventors">
                                (72)
                            </dt>
                            <dd>
                                <%= data.get_inventors(true).map(function(item) { return '' + item + ''; }).join('<br/>') %>
                            </dd>

                            <dt class="inid-tooltip" data-toggle="tooltip" title="ipc classes">
                                (51)
                            </dt>
                            <dd>
                                <%= data.get_ipc_list(true).join(', ') %>
                            </dd>

                            <br/>

                            <dt class="inid-tooltip" data-toggle="tooltip" title="abstract">
                                (57)
                            </dt>
                            <dd>
                                <div class="abstract">
                                    <%= abstract_list.join('<br/><br/>') %>
                                </div>
                            </dd>

                            <br/>

                            <dt class="inid-tooltip" data-toggle="tooltip" title="references cited">
                                (56)
                            </dt>
                            <dd>
                                <%= data.get_patent_citation_list(true).join(', ') %>
                                <br/><br/>
                                <table class="table table-striped table-condensed">
                                    <%= data.get_npl_citation_list().map(function(item) { return '<tr><td>' + item + '</td></tr>'; }).join('') %>
                                </table>
                            </dd>

                        </dl>

                        <!-- embed 3rd-party component -->
                        <div class="embed-item" data-embed-url="<%= embed_item_url %>" data-document-number="<%= patent_number %>">
                        </div>

                    </div>
                </div>

             </div>
        </div>
        </%text>

</script>


<script id="backend-error-template" type="text/x-underscore-template">

    <div class="alert alert-error alert-block">
        <button type="button" class="close" data-dismiss="alert">&times;</button>
        <h4>ERROR</h4>
        <%text>

        <dl class="dl-horizontal dl-horizontal-biblio2">

            <dt>
                Message
            </dt>
            <dd>
                <h4><%= description['content'] %></h4>
            </dd>

            <br/>

            <dt>
                Date
            </dt>
            <dd>
                <%= description['headers']['date'] %>
            </dd>

            <dt>
                Status
            </dt>
            <dd>
                <%= description['status_code'] %> <%= description['reason'] %>
            </dd>

            <dt>
                Name
            </dt>
            <dd>
                <%= name %>
            </dd>

            <dt>
                Location
            </dt>
            <dd>
                <%= location %>
            </dd>

            <dt>
                URL
            </dt>
            <dd>
                <%= description['url'] %>
            </dd>

        </dl>
        </%text>

    </div>

</script>


<script id="cornice-error-template" type="text/x-underscore-template">

    <div class="alert alert-error alert-block">
        <button type="button" class="close" data-dismiss="alert">&times;</button>
        <h4>ERROR</h4>
        <%text>

        <dl class="dl-horizontal dl-horizontal-biblio2">

            <dt>
                Message
            </dt>
            <dd>
                <h4><%= description %></h4>
            </dd>

            <br/>

            <dt>
                Name
            </dt>
            <dd>
                <%= name %>
            </dd>

            <dt>
                Location
            </dt>
            <dd>
                <%= location %>
            </dd>

        </dl>
        </%text>

    </div>

</script>


<script id="alert-template" type="text/x-underscore-template">
    <%text>
    <div class="alert alert-block <%= clazz %>">
        <button type="button" class="close" data-dismiss="alert">&times;</button>
        <h4><%= title %></h4>
        <br/>
        <%= description %>
    </div>
    </%text>
</script>


<script id="cql-field-chooser-entry" type="text/x-underscore-template">
<%text>

    <div class="row-fluid">
        <div class="span5 strong">
            <%= label %>
        </div>
        <div class="span4">
            <%= _(fields).first() %>
            <br/>
            <small><%= _(fields).rest(1).join('<br/>') %></small>
        </div>
        <div class="span3">
            <%= more %>
        </div>
    </div>

</%text>
</script>

<%include file="basket.html"/>


<script type="text/javascript" src="/static/js/lib/jquery.caret-1.5.1.min.js"></script>
<script type="text/javascript" src="/static/js/lib/jquery.hotkeys.js"></script>
<script type="text/javascript" src="/static/js/lib/localforage.min.js"></script>
<script type="text/javascript" src="/static/js/lib/backbone.localforage.min.js"></script>
<script type="text/javascript" src="/static/js/lib/jquery-keyword-highlight.js"></script>

<link rel="stylesheet" type="text/css" href="/static/css/app.css" />

% if request.registry.settings.get('ipsuite.production') == 'true':
    <script type="text/javascript" src="/static/js/app.min.js"></script>
% else:
    <script type="text/javascript" src="/static/js/app/components/basket.js"></script>
    <script type="text/javascript" src="/static/js/app/core.js"></script>
    <script type="text/javascript" src="/static/js/app/ops-sdk.js"></script>
    <script type="text/javascript" src="/static/js/app/models/ops.js"></script>
    <script type="text/javascript" src="/static/js/app/models/depatisnet.js"></script>
    <script type="text/javascript" src="/static/js/app/main.js"></script>
% endif

</%block>
