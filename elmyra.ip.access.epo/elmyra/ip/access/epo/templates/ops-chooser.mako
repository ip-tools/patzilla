## -*- coding: utf-8 -*-

<%inherit file="site.mako" />

<%block name="body">

## http://bootsnipp.com/snipps/e-mail-interface-like-gmail
## http://davidsulc.com/blog/2012/04/15/a-simple-backbone-marionette-tutorial/
## https://github.com/davidsulc/backbone.marionette-collection-example

<div class="container">
    <div class="table-responsive">
        <div id="ops-collection-region"/>
    </div>
</div>

<%text>
<script type="text/x-underscore-template" id="ops-collection-template">
    <thead>
        <tr>
        <th class="span1"><input type="checkbox" title="Alle auswählen"/></th>
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
        var title = data['bibliographic-data']['invention-title']['$'];
        var publication_date = data['bibliographic-data']['publication-reference']['document-id'][0]['date']['$'];

        var applicant_list = _.map(data['bibliographic-data']['parties']['applicants']['applicant'], function(applicant) {
            return applicant['applicant-name']['name']['$'];
        });
        applicant_list = data.get_applicants();

        var ipc_node = data['bibliographic-data']['classifications-ipcr']['classification-ipcr'];
        if (!_.isArray(ipc_node)) {
            ipc_node = [ipc_node];
        }
        var ipc_list = _.map(ipc_node, function(ipc) {
            return ipc['text']['$'];
        });

        var abstract_node = data['abstract']['p'];
        if (!_.isArray(abstract_node)) {
            abstract_node = [abstract_node];
        }
        var abstract = '[' + data['abstract']['@lang'] + '] ' + abstract_node.map(function(node) { return node['$']; }).join(' ');

        %>

        <td><input type="checkbox"/></td>
        <td><strong><%= patent_number %></strong></td>
        <td>
            <table class="table table-condensed table-clear-border-vertical">
                <tbody>
                    <tr>
                        <td class="span2"><i class="icon-file-text-alt"></i>&nbsp; Titel</td>
                        <td><%= title %></td>
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
                        <td><div class="abstract"><%= abstract %></div></td>
                    </tr>
                </tbody>
            </table>
        </td>

</script>
</%text>

<link rel="stylesheet" type="text/css" href="/static/css/ops-chooser.css" />
<script type="text/javascript" src="/static/ops-chooser.js"></script>

</%block>
