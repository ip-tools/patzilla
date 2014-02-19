## -*- coding: utf-8 -*-

<%inherit file="site.mako" />

<%block name="body">

## http://bootsnipp.com/snipps/e-mail-interface-like-gmail
## http://davidsulc.com/blog/2012/04/15/a-simple-backbone-marionette-tutorial/
## https://github.com/davidsulc/backbone.marionette-collection-example

<%
query = request.params.get('query', '')
numberlist = '\n'.join(request.params.get('numberlist', '').split(','))
html_title = request.params.get('html-title', 'Patent search for "{0}"'.format(query))
page_title = request.params.get('page-title', 'Patent search')
page_subtitle = request.params.get('page-subtitle', '')
page_footer = request.params.get('page-footer', 'data source: epo/ops')
app_productname = request.params.get('app-productname', 'elmyra <i class="circle-icon">IP</i> suite')
app_versionstring = request.params.get('app-versionstring', 'release 0.2.0')
ship_mode = request.params.get('ship-mode', 'multi-numberlist')
ship_param = request.params.get('ship-param', request.params.get('ship_param', 'payload'))
ship_url = request.params.get('ship-url', request.params.get('ship_url', ''))
ship_frame = request.params.get('ship-frame', 'opsbrowser_right_frame')
%>
<script type="application/javascript">
var ship_mode = '${ship_mode}';
var ship_param = '${ship_param}';
var ship_url = '${ship_url}';
var ship_frame = '${ship_frame}';
</script>

## title / headline
<div class="container-fluid">
    <div class="span8">
        <div class="pull-left">
        <h3 style="display: inline-block">${page_title}</h3>
        &nbsp;&nbsp;&nbsp;
        ${page_subtitle}
        &nbsp;&nbsp;&nbsp;
        <i class="icon-refresh icon-spin icon-large" style="display: none" id="spinner"></i>
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
    <div class="row-fluid well" id="querybuilder-basket-area" style="padding: 0px;">
        <div class="span8" id="querybuilder-area" style="padding: 1em">
            <h6 style="display: inline">
                <a href="https://en.wikipedia.org/wiki/Contextual_Query_Language" target="_blank">About CQL</a>
            </h6>
            <br/>
            <textarea class="span12" id="query" name="query" placeholder="CQL expression" rows="5">${query}</textarea>
            <br/>
            <input id="query-button" type="button" class="btn btn-info btn-popover"
                type="button" role="button" value="Send query"
                data-toggle="popover" data-trigger="hover" data-placement="right" data-content="Send query to database"
            />
        </div>
        % if ship_mode != 'single-bibdata':
        <div class="span4 container-fluid" id="basket-area" style="padding: 1em">
            <div class="row-fluid">
                <div class="span12">
                    <h6 style="display: inline">
                        Your selection
                    </h6>
                    <br/>
                    <textarea class="span12" id="basket" name="${ship_param}" rows="5">${numberlist}</textarea>
                </div>
            </div>
            <div class="row-fluid">
                <div class="span6">
                    <form id="basket-form" name="basket-form" method="post" action="${ship_url}">
                        <input id="basket-submit-button" class="btn btn-info btn-popover" ${ship_url or 'disabled="disabled"'}
                            type="submit" role="button" value="Submit"
                            data-toggle="popover" data-trigger="hover" data-placement="bottom" data-content="Submit selected documents to origin or 3rd-party system"
                        />
                    </form>
                </div>
                <div class="span6">
                    <a id="basket-review-button" role="button" class="btn btn-info btn-popover pull-right"
                        data-toggle="popover" data-trigger="hover" data-placement="bottom" data-content="Review selected documents"
                        >
                        Review
                    </a>
                </div>
            </div>
        </div>
        % endif
    </div>


    ## pager
    <div id="ops-pagination-region"></div>

    <div id="alert-area"></div>

    ## results
    <div id="ops-collection-region"></div>

    <hr class="clear-margin" style="margin-top: 50px"/>
    <div class="page-footer pull-left">
        &copy; 2013-2014, Elmyra UG — All rights reserved.
    </div>
    <div class="page-footer pull-right">
        <small>
            ${page_footer},
            ${app_versionstring}
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



## pager template
<%text>
<script type="text/x-underscore-template" id="ops-pagination-template">
    <div class="pull-left">
        Result count: <span class="badge badge-info"><%= result_count| 0 %></span>
    </div>
    <div class="pagination pagination-centered">
      <ul>
        <!--
        <li><a href="#" action="previous">Prev</a></li>
        -->
        <li><a href="#" range="1-25">1-25</a></li>
        <li><a href="#" range="26-50">26-50</a></li>
        <li><a href="#" range="51-75">51-75</a></li>
        <li><a href="#" range="76-100">76-100</a></li>
        <li><a href="#" range="101-125">101-125</a></li>
        <li><a href="#" range="126-150">126-150</a></li>
        <li><a href="#" range="151-175">151-175</a></li>
        <li><a href="#" range="176-200">176-200</a></li>
        <!--
        <li><a href="#" action="next">Next</a></li>
        -->
      </ul>
    </div>
</script>
</%text>


## result list template
<script id="ops-collection-template" type="text/x-underscore-template">
    <!--
    <div id="ops-collection-entry" class="row"/>
    -->
</script>


## result item template
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

        var patent_number = data['@country'] + data['@doc-number'] + data['@kind'];
        var applicant_list = data.get_applicants();
        var inventor_list = data.get_inventors();
        var drawing_url = data.get_drawing_url();
        var fullimage_url = data.get_fullimage_url();
        var espacenet_pdf_url = data.get_espacenet_pdf_url();

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

        // ipc
        var ipc_list = [];
        var ipc_node_top = data['bibliographic-data']['classifications-ipcr'];
        if (ipc_node_top) {
            var ipc_node = to_list(ipc_node_top['classification-ipcr']);
            ipc_list = _.map(ipc_node, function(ipc) {
                return ipc['text']['$'];
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
        <div class="container-fluid ops-collection-entry">

            <div class="ops-collection-entry-heading row-fluid">

                <!-- patent number -->
                <div class="span5">
                    <h3 class="header-compact"><%= patent_number %></h3>
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
                                <%= publication_date %>
                            </dd>
                        </dl>
                    </div>
                </div>

                <!-- actions -->
                <div class="span3 container-fluid pull-right">
                    <div class="span6">
                        <a href="#ops-pdf-modal" data-toggle="modal" role="button" class="btn pdf-open btn-popover hide"
                            data-patent-number="<%= patent_number %>" data-pdf-url="<%= fullimage_url %>"
                            data-toggle="popover" data-trigger="hover" data-placement="bottom" data-content="View PDF document"
                            >
                            <img src="/static/img/icons/pdf.svg" width="20"/>
                            &nbsp;
                            PDF
                        </a>
                        <a href="<%= espacenet_pdf_url %>" target="_blank" role="button" class="btn btn-popover pdf-download"
                            data-toggle="popover" data-trigger="hover" data-placement="bottom" data-content="Download PDF document"
                            >
                            <img src="/static/img/icons/pdf.svg" width="20"/>
                            &nbsp;
                            PDF
                        </a>
                    </div>
                    <div class="span6">
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
                        <%text>
                    </div>
                </div>

            </div>

            <div class="ops-collection-entry-inner container-fluid">

                <div class="row-fluid">
                    <div class="span12">
                        <strong><%= title_list.join('<br/>') %></strong>
                    </div>
                </div>

                <div class="row-fluid">
                    <div class="span5">
                        <img src="<%= drawing_url %>" alt="No drawing available."/>
                    </div>
                    <div class="span7">

                        <dl class="dl-horizontal dl-horizontal-biblio">

                            <dt class="inid-tooltip" data-toggle="tooltip" title="applicants">
                                (71)
                            </dt>
                            <dd>
                                <%= applicant_list.map(function(item) { return '<strong>' + item + '</strong>'; }).join('<br/>') %>
                                &nbsp;
                            </dd>

                            <dt class="inid-tooltip" data-toggle="tooltip" title="inventors">
                                (72)
                            </dt>
                            <dd>
                                <%= inventor_list.map(function(item) { return '' + item + ''; }).join('<br/>') %>
                                &nbsp;
                            </dd>

                            <dt class="inid-tooltip" data-toggle="tooltip" title="ipc classes">
                                (51)
                            </dt>
                            <dd>
                                <%= ipc_list.join(', ') %>
                                &nbsp;
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

                        </dl>

                    </div>
                </div>

             </div>
        </div>
        </%text>


        % if ship_mode == 'single-bibdata':
        <%text>
        <td>
            <form name="single-bibdata-<%= patent_number %>" method="post" action="<%= ship_url %>" target="<%= ship_frame %>">
                <input name="query" type="hidden" value="${query}"/>
                <input name="patent_number" type="hidden" value="<%= patent_number %>"/>
                <input name="title" type="hidden" value="<%= title_list.join('\n') %>"/>
                <input name="applicants" type="hidden" value="<%= applicant_list.join('\n') %>"/>
                <input name="inventors" type="hidden" value="<%= inventor_list.join('\n') %>"/>
                <input name="application_date" type="hidden" value="<%= application_date %>"/>
                <input name="publication_date" type="hidden" value="<%= publication_date %>"/>
                <input name="ipcs" type="hidden" value="<%= ipc_list.join('\n') %>"/>
                <input name="abstract" type="hidden" value="<%= abstract_list.join('\n') %>"/>
                <input name="ship_action" type="submit" value="rate"/>
            </form>
        </td>
        </%text>
        % endif

</script>


<script id="backend-error-template" type="text/x-underscore-template">

    <div class="alert alert-error alert-block">
        <button type="button" class="close" data-dismiss="alert">&times;</button>
        <h4>ERROR</h4>
        <%text>

        <dl class="dl-horizontal dl-horizontal-biblio2">

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
                Message
            </dt>
            <dd>
                <%= description['content'] %>
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


<link rel="stylesheet" type="text/css" href="/static/css/ops-chooser.css" />
<script type="text/javascript" src="/static/js/pdfobject.min.js"></script>
<script type="text/javascript" src="/static/js/ops-chooser.js"></script>

</%block>
