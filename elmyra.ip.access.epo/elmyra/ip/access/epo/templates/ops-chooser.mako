## -*- coding: utf-8 -*-

<%inherit file="site.mako" />

<%block name="body">

## http://bootsnipp.com/snipps/e-mail-interface-like-gmail
## http://davidsulc.com/blog/2012/04/15/a-simple-backbone-marionette-tutorial/
## https://github.com/davidsulc/backbone.marionette-collection-example


<div class="container span12 pull-left">
    <h1>Patentrecherche <small>via EPO/OPS</small></h1>

    <div id="ops-query">
        <div class="container well">
            <div class="pull-left">
                <h6 style="display: inline">
                    <a href="https://en.wikipedia.org/wiki/Contextual_Query_Language" target="_blank">Über CQL</a>
                </h6>
                <br/>
                <textarea class="span9" id="query" name="query" placeholder="CQL Anfrage" rows="5">${request.params.get('query', '')}</textarea>
                <br/>
                <input id="query-button" type="button" class="btn btn-info" value="Datenbank abfragen"/>
            </div>
            <div class="pull-right">
                <h6 style="display: inline">
                    Auswahl
                </h6>
                <br/>
                <form id="basket-form" name="basket-form" method="post" action="${request.params.get('ship_url', '')}">
                    <textarea class="span3" id="basket" name="${request.params.get('ship_param', 'payload')}" rows="5"></textarea>
                    <br/>
                    <input id="basket-button" type="submit" class="btn btn-info" ${request.params.get('ship_url') or 'disabled="disabled"'} value="Übermitteln"/>
                </form>
            </div>
        </div>
    </div>

    <div id="ops-pagination-region" class="span12"></div>

    <div class="table-responsive">
        <div id="ops-collection-region" class="span12"></div>
    </div>

</div>

<%text>
<script type="text/x-underscore-template" id="ops-pagination-template">
    <div class="pagination pagination-centered">
      <div class="pull-left">
        <div class="span1">
        <i class="icon-refresh icon-spin icon-large pull-left hide" id="spinner"></i>
        </div>
      </div>
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

<%text>
<script type="text/x-underscore-template" id="ops-collection-template">
    <thead>
        <tr>
        <th class="span1"><input type="checkbox" id="all-check" title="Alle auswählen"/></th>
        <th class="span2">Patentnummer</th>
        <th class="span9">Bibliographische Daten</th>
        </tr>
    </thead>
    <tbody id="ops-collection-tbody">
    </tbody>
</script>
</%text>

<%text>
<script type="text/x-underscore-template" id="ops-entry-template">
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

        <td><input type="checkbox" id="patent-number-<%= patent_number %>" class="patent-number" value="<%= patent_number %>"/></td>
        <td><strong><%= patent_number %></strong></td>
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

</script>
</%text>

<link rel="stylesheet" type="text/css" href="/static/css/ops-chooser.css" />
<script type="text/javascript" src="/static/js/ops-chooser.js"></script>

</%block>
