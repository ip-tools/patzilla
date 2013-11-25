## -*- coding: utf-8 -*-

<%inherit file="site.mako" />

<%block name="body">

## http://bootsnipp.com/snipps/e-mail-interface-like-gmail
## http://davidsulc.com/blog/2012/04/15/a-simple-backbone-marionette-tutorial/
## https://github.com/davidsulc/backbone.marionette-collection-example

<%
query = request.params.get('query', '')
page_title = request.params.get('page-title', 'Patentrecherche')
page_subtitle = request.params.get('page-subtitle', 'via EPO/OPS, ops/browser 0.0.8')
ship_mode = request.params.get('ship-mode', 'multi-numberlist')
ship_param = request.params.get('ship-param', request.params.get('ship_param', 'payload'))
ship_url = request.params.get('ship-url', request.params.get('ship_url', '#'))
ship_frame = request.params.get('ship-frame', 'opsbrowser_right_frame')
%>
<script type="application/javascript">
var ship_mode = '${ship_mode}';
var ship_param = '${ship_param}';
var ship_url = '${ship_url}';
var ship_frame = '${ship_frame}';
</script>

## title / headline
<div class="container-fluid span12">
    <blockquote>
        <p>
            <h2 style="display: inline">${page_title}</h2>
            &nbsp;&nbsp;&nbsp;<i class="icon-refresh icon-spin icon-large" style="display: none" id="spinner"></i>
        </p>
        <small>${page_subtitle}</small>
    </blockquote>
</div>

<div class="container-fluid span12">

    ## query builder and basket
    <div class="row-fluid well" id="querybuilder-basket-area" style="padding: 0px;">
        <div class="span8" id="querybuilder-area" style="padding: 1em">
            <h6 style="display: inline">
                <a href="https://en.wikipedia.org/wiki/Contextual_Query_Language" target="_blank">Über CQL</a>
            </h6>
            <br/>
            <textarea class="span12" id="query" name="query" placeholder="CQL Anfrage" rows="5">${query}</textarea>
            <br/>
            <input id="query-button" type="button" class="btn btn-info" value="Datenbank abfragen"/>
        </div>
        % if ship_mode != 'single-bibdata':
        <div class="span4" id="basket-area" style="padding: 1em">
            <h6 style="display: inline">
                Auswahl
            </h6>
            <br/>
            <form id="basket-form" name="basket-form" method="post" action="${ship_url}">
                <textarea class="span12" id="basket" name="${ship_param}" rows="5"></textarea>
                <br/>
                <input id="basket-button" type="submit" class="btn btn-info" ${ship_url or 'disabled="disabled"'} value="Übermitteln"/>
            </form>
        </div>
        % endif
    </div>


    ## pager
    <div id="ops-pagination-region"></div>


    ## results
    <div id="ops-collection-region"></div>

</div>


## pager template
<%text>
<script type="text/x-underscore-template" id="ops-pagination-template">
    <div class="pull-left">
        Treffer: <%= result_count %>
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
<script type="text/x-underscore-template" id="ops-collection-template">
    <thead>
        <tr>
        % if ship_mode == 'multi-numberlist':
        <th class="span1"><input type="checkbox" id="all-check" title="Alle auswählen"/></th>
        % endif
        <th class="span2">Patentnummer</th>
        <th class="span9">Bibliographische Daten</th>
        % if ship_mode == 'single-bibdata':
        <th class="span1"></th>
        % endif
        </tr>
    </thead>
    <tbody id="ops-collection-tbody">
    </tbody>
</script>


## result item template
<script type="text/x-underscore-template" id="ops-entry-template">

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


        // 2.2 prepare some template variables

        var patent_number = data['@country'] + data['@doc-number'] + data['@kind'];
        var applicant_list = data.get_applicants();
        var inventor_list = data.get_inventors();
        var firstpage_url = data.get_firstpage_url();

        var publication_date = search_date(data['bibliographic-data']['publication-reference']['document-id']);
        var application_date = search_date(data['bibliographic-data']['application-reference']['document-id']);

        // title
        var title_node = to_list(data['bibliographic-data']['invention-title']);
        var title_list = _.map(title_node, function(title) {
            var lang_prefix = title['@lang'] && '[' + title['@lang'] + '] ' || '';
            return lang_prefix + title['$'];
        });

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
                var lang_prefix = node['@lang'] && '[' + node['@lang'] + '] ' || '';
                return lang_prefix + text;
            });
        }

        %>
        </%text>

        % if ship_mode == 'multi-numberlist':
        <%text>
        <td><input type="checkbox" id="chk-patent-number-<%= patent_number %>" class="chk-patent-number" value="<%= patent_number %>"/></td>
        </%text>
        % endif

        <%text>
        <td>
            <strong><%= patent_number %></strong>
            <!--
            <br/>
            <img src="<%= firstpage_url %>"/>
            -->
        </td>

        <td>
            <table class="table table-condensed table-clear-border-vertical">
                <tbody>
                    <tr>
                        <td class="span2"><i class="icon-file-text-alt"></i>&nbsp; Titel</td>
                        <td><strong><%= title_list.join('<br/>') %></strong></td>
                    </tr>
                    <tr>
                        <td><i class="icon-group"></i> Anmelder</td>
                        <td>
                            <ul>
                            <%= applicant_list.map(function(item) { return '<li>' + item + '</li>'; }).join('') %>
                            </ul>
                        </td>
                    </tr>
                    <tr>
                        <td><i class="icon-group"></i> Erfinder</td>
                        <td>
                            <ul>
                            <%= inventor_list.map(function(item) { return '<li>' + item + '</li>'; }).join('') %>
                            </ul>
                        </td>
                    </tr>
                    <tr>
                        <td><i class="icon-calendar"></i>&nbsp; Anm.-Datum</td>
                        <td><%= application_date %></td>
                    </tr>
                    <tr>
                        <td><i class="icon-calendar"></i>&nbsp; Pub.-Datum</td>
                        <td><%= publication_date %></td>
                    </tr>
                    <tr>
                        <td><i class="icon-tag"></i>&nbsp; IPC</td>
                        <td><%= ipc_list.join(', ') %></td>
                    </tr>
                    <tr>
                        <td><i class="icon-align-justify"></i>&nbsp; Beschreibung</td>
                        <td><div class="abstract"><%= abstract_list.join('<br/><br/>') %></div></td>
                    </tr>
                </tbody>
            </table>
        </td>
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
                <input name="ship_action" type="submit" value="bewerten"/>
            </form>
        </td>
        </%text>
        % endif

</script>

<link rel="stylesheet" type="text/css" href="/static/css/ops-chooser.css" />
<script type="text/javascript" src="/static/js/ops-chooser.js"></script>

</%block>
