## -*- coding: utf-8 -*-

<%inherit file="site.mako" />

<%block name="body">

<link rel="stylesheet" type="text/css" href="/static/css/ops-chooser.css" />
<script type="text/javascript" src="/static/ops-chooser.js"></script>

## http://bootsnipp.com/snipps/e-mail-interface-like-gmail
## http://davidsulc.com/blog/2012/04/15/a-simple-backbone-marionette-tutorial/
## https://github.com/davidsulc/backbone.marionette-collection-example

<div class="container">
    <div class="table-responsive">
        <div id="ipdocumentcollection-region"/>
    </div>
</div>

<%text>
<script type="text/template" id="ipdocumentcollection-template">
    <thead>
        <tr>
        <th class="span1"><input type="checkbox" title="Alle auswählen"/></th>
        <th class="span2">Patentnummer</th>
        <th class="span9">Bibliographische Daten</th>
        </tr>
    </thead>
    <tbody id="ipdocumentcollection-tbody">
    </tbody>
</script>
</%text>

<%text>
<script type="text/template" id="ipdocument-template">
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
                        <td><%= applicant %></td>
                    </tr>
                    <tr>
                        <td><i class="icon-calendar"></i>&nbsp; Pub.-Datum</td>
                        <td><%= publication_date %></td>
                    </tr>
                    <tr>
                        <td><i class="icon-tag"></i>&nbsp; IPC</td>
                        <td><%= ipc %></td>
                    </tr>
                </tbody>
            </table>

        </td>
</script>
</%text>

</%block>
