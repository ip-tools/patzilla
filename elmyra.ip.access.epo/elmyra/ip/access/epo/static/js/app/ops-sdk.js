// -*- coding: utf-8 -*-
// (c) 2013,2014 Andreas Motl, Elmyra UG

function cql_field_chooser_text(label, fields, more) {

    // short-circuit enrichment
    //return label;

    var tpl = _.template($('#cql-field-chooser-entry').html());
    fields = fields.map(function(item) { return item + '=' });
    var html = tpl({label: label, fields: fields, more: more});
    return html;
}

var OPS_CQL_FIELDS = [
    {
        text: '<h4>Popular</h4>',
        children: [
            { id: 'num', text: cql_field_chooser_text('Publication-, application- or<br/>priority number', ['num'], '(10, 11, 21, 31)') },
            { id: 'txt', text: cql_field_chooser_text('Title, abstract, inventor-, or applicant name', ['txt'], '(54, 57, 72, 71, 73)') },
            { id: 'cl', text: cql_field_chooser_text('CPC or IPC8 class', ['cl'], '') },
        ],
    },
    {
        text: '<h4>Publication</h4>',
        children: [
            { id: 'pn', text: cql_field_chooser_text('Publication number', ['pn', 'publicationnumber'], '(10, 11)') },
            { id: 'pd', text: cql_field_chooser_text('Publication date', ['pd', 'publicationdate'], '') },
            { id: 'pa', text: cql_field_chooser_text('Applicant', ['pa', 'applicant'], '(71, 73)') },
            { id: 'in', text: cql_field_chooser_text('Inventor', ['in', 'inventor'], '(72)') },
            { id: 'ia', text: cql_field_chooser_text('Inventor or applicant', ['ia', 'inventorandapplicant'], '(72, 71, 73)') },
            { id: 'spn', text: cql_field_chooser_text('Publication number<br/><small>in epodoc format</small>', ['spn'], '') },
        ],
    },
    {
        text: '<h4>Text</h4>',
        children: [
            { id: 'ti', text: cql_field_chooser_text('Title', ['ti', 'title'], '(54)') },
            { id: 'ab', text: cql_field_chooser_text('Abstract', ['ab', 'abstract'], '(57)') },
            { id: 'ta', text: cql_field_chooser_text('Title or abstract', ['ta', 'titleandabstract'], '(54, 57)') },
            { id: 'txt', text: cql_field_chooser_text('Title, abstract, inventor-, or applicant name', ['txt'], '(54, 57, 72, 71, 73)') },
        ],
    },
    {
        text: '<h4>Application, priority and family</h4>',
        children: [
            { id: 'ap', text: cql_field_chooser_text('Application number', ['ap', 'applicantnumber'], '(21)') },
            { id: 'sap', text: cql_field_chooser_text('Application number<br/><small>in epodoc format</small>', ['sap'], '') },
            { id: 'pr', text: cql_field_chooser_text('Priority number', ['pr', 'prioritynumber'], '(31)') },
            { id: 'spr', text: cql_field_chooser_text('Priority number<br/><small>in epodoc format</small>', ['spr'], '') },
            { id: 'famn', text: cql_field_chooser_text('Family identifier (simple)', ['famn'], '') },
        ],
    },
    {
        text: '<h4>Classification</h4>',
        children: [
            { id: 'cpc', text: cql_field_chooser_text('CPC classification<br/><small>(invention and additional)</small>', ['cpc', 'cpci', 'cpca'], '') },
            { id: 'ipc', text: cql_field_chooser_text('IPC8 class', ['ipc', 'ic'], '') },
            { id: 'ci', text: cql_field_chooser_text('IPC8 core invention class', ['ci'], '') },
            { id: 'cn', text: cql_field_chooser_text('IPC8 core additional class<br/><small>(non-invention)</small>', ['cn'], '') },
            { id: 'ai', text: cql_field_chooser_text('IPC8 advanced invention class', ['ai'], '') },
            { id: 'an', text: cql_field_chooser_text('IPC8 advanced additional class<br/><small>(non-invention)</small>', ['an'], '') },
            { id: 'a', text: cql_field_chooser_text('IPC8 advanced class', ['a'], '') },
            { id: 'c', text: cql_field_chooser_text('IPC8 core class', ['c'], '') },
            { id: 'cl', text: cql_field_chooser_text('CPC or IPC8 class', ['cl'], '') },
        ],
    },
    {
        text: '<h4>Citations</h4>',
        children: [
            { id: 'ct', text: cql_field_chooser_text('Cited document number', ['ct', 'citation'], '(56)') },
            { id: 'ex', text: cql_field_chooser_text('Cited document number<br/><small>during examination</small>', ['ex'], '') },
            { id: 'op', text: cql_field_chooser_text('Cited document number<br/><small>during opposition</small>', ['op'], '') },
            { id: 'rf', text: cql_field_chooser_text('Cited document number<br/><small>provided by applicant</small>', ['rf'], '') },
            { id: 'oc', text: cql_field_chooser_text('Another cited document number', ['oc'], '') },
        ],
    },
];
