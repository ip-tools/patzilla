## -*- coding: utf-8 -*-

<%inherit file="site.mako" />

<%block name="body">

## http://bootsnipp.com/snipps/e-mail-interface-like-gmail
## http://davidsulc.com/blog/2012/04/15/a-simple-backbone-marionette-tutorial/
## https://github.com/davidsulc/backbone.marionette-collection-example


<div class="container pull-left">
    <h1>Patentrecherche <small>via EPO/OPS</small></h1>
    <div id="ops-query">
        <div class="container well">
            <div class="pull-left">
                <h6 style="display: inline">
                    <a href="https://en.wikipedia.org/wiki/Contextual_Query_Language" target="_blank">Über CQL</a>
                </h6>
                <br/>
                <textarea class="span6" id="query" name="query" placeholder="CQL Anfrage" rows="5"></textarea>
                <br/>
                <input id="query-button" type="button" class="btn btn-info" value="Datenbank abfragen"></input>
            </div>
            <div class="pull-right">
                <h6 style="display: inline">
                    Auftrag
                </h6>
                <br/>
                <form id="basket-form" name="basket-form" method="post">
                    <textarea class="span6" id="basket" name="NumberList" rows="5"></textarea>
                    <br/>
                    <input id="basket-button" type="button" class="btn btn-info" value="Übermitteln"></input>
                    <input id="basket-came-from" type="text" class="span4" value=""></input>
                </form>
            </div>
            <br/>
        </div>
    </div>
    <div class="table-responsive">
        <div id="ops-collection-region"/>
    </div>
</div>

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


        // 2. prepare some template variables

        var patent_number = data['@country'] + data['@doc-number'] + data['@kind'];
        var publication_date = data['bibliographic-data']['publication-reference']['document-id'][0]['date']['$'];
        var applicant_list = data.get_applicants();

        // title
        var title_node = data['bibliographic-data']['invention-title'];
        if (!_.isArray(title_node)) {
            title_node = [title_node];
        }
        var title_list = _.map(title_node, function(title) {
            return '[' + title['@lang'] + '] ' + title['$'];
        });

        // ipc
        var ipc_node_top = data['bibliographic-data']['classifications-ipcr'];
        if (ipc_node_top) {
            var ipc_node = ipc_node_top['classification-ipcr'];
            if (!_.isArray(ipc_node)) {
                ipc_node = [ipc_node];
            }
            var ipc_list = _.map(ipc_node, function(ipc) {
                return ipc['text']['$'];
            });
        }

        var abstract_node = data['abstract'];
        if (!_.isArray(abstract_node)) {
            abstract_node = [abstract_node];
        }
        var abstract_list = abstract_node.map(function(node) { return '[' + node['@lang'] + '] ' + node['p']['$']; });

        %>

        <td><input type="checkbox" name="patent_number" class="patent_number" value="<%= patent_number %>"/></td>
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
                        <td><i class="icon-calendar"></i>&nbsp; Pub.-Datum</td>
                        <td><%= publication_date %></td>
                    </tr>
                    <tr>
                        <td><i class="icon-tag"></i>&nbsp; IPC</td>
                        <td><%= ipc_list.join(', ') %></td>
                    </tr>
                    <tr>
                        <td><i class="icon-align-justify"></i>&nbsp; Beschreibung</td>
                        <td><div class="abstract"><%= abstract_list.join('<br/>') %></div></td>
                    </tr>
                </tbody>
            </table>
        </td>

</script>
</%text>

<link rel="stylesheet" type="text/css" href="/static/css/ops-chooser.css" />
<script type="text/javascript" src="/static/ops-chooser.js"></script>

</%block>
