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

var DEPATISNET_CQL_FIELDS = [
    {
        text: '<h4>Publication</h4>',
        children: [
            { id: 'pn', text: cql_field_chooser_text('Publication number', ['pn'], '(10, 11)') },
            { id: 'pc', text: cql_field_chooser_text('Country of publication', ['pc'], '(19)') },
            { id: 'pub', text: cql_field_chooser_text('Publication date', ['pub'], '') },
            { id: 'py', text: cql_field_chooser_text('Publication year', ['py'], '') },
            { id: 'pa', text: cql_field_chooser_text('Applicant/Owner', ['pa'], '(71, 73)') },
            { id: 'in', text: cql_field_chooser_text('Inventor', ['in'], '(72)') },
            { id: 'pcod', text: cql_field_chooser_text('Kind code', ['pcod'], '(12)') },
        ],
    },
    {
        text: '<h4>Text</h4>',
        children: [
            { id: 'ti', text: cql_field_chooser_text('Title', ['ti'], '(54)') },
            { id: 'ab', text: cql_field_chooser_text('Abstract', ['ab'], '(57)') },
            { id: 'de', text: cql_field_chooser_text('Description', ['de'], '') },
            { id: 'cl', text: cql_field_chooser_text('Claims', ['cl'], '(57)') },
            { id: 'bi', text: cql_field_chooser_text('Full text data', ['bi']) },
        ],
    },
    {
        text: '<h4>Application</h4>',
        children: [
            { id: 'an', text: cql_field_chooser_text('Application number', ['ap'], '(21)') },
            { id: 'ac', text: cql_field_chooser_text('Country of application', ['ac'], '') },
            { id: 'ad', text: cql_field_chooser_text('Application date', ['ad'], '(22, 96)') },
            { id: 'ay', text: cql_field_chooser_text('Application year', ['ay'], '') },
        ],
    },
    {
        text: '<h4>Priority</h4>',
        children: [
            { id: 'prn', text: cql_field_chooser_text('Priority number', ['prn'], '(31)') },
            { id: 'prc', text: cql_field_chooser_text('Country of priority', ['prc'], '(33)') },
            { id: 'prd', text: cql_field_chooser_text('Priority date', ['prd'], '(32)') },
            { id: 'pry', text: cql_field_chooser_text('Priority year', ['pry'], '') },
        ],
    },
    {
        text: '<h4>Citations</h4>',
        children: [
            { id: 'ct', text: cql_field_chooser_text('Cited documents', ['ct'], '(56)') },
            { id: 'ctnp', text: cql_field_chooser_text('Cited non-patent literature', ['ctnp'], '(56)') },
        ],
    },
    {
        text: '<h4>All IPC</h4>',
        children: [
            { id: 'ic', text: cql_field_chooser_text('All IPC fields', ['ic'], '') },
        ],
    },
    {
        text: '<h4>Bibliographic IPC</h4>',
        children: [
            { id: 'icb', text: cql_field_chooser_text('Bibliographic IPC', ['icb'], '') },
            { id: 'icm', text: cql_field_chooser_text('IPC main class', ['icm'], '(51)') },
            { id: 'ics', text: cql_field_chooser_text('IPC secondary class', ['ics'], '(51)') },
            { id: 'ica', text: cql_field_chooser_text('IPC additional class', ['ica'], '') },
            { id: 'ici', text: cql_field_chooser_text('IPC index classes', ['ici'], '') },
            { id: 'icmv', text: cql_field_chooser_text('IPC main class version', ['icmv'], '') },
            { id: 'icsv', text: cql_field_chooser_text('IPC secondary class version', ['icsv'], '') },
            { id: 'icav', text: cql_field_chooser_text('IPC additional class version', ['icav'], '') },
            { id: 'icml', text: cql_field_chooser_text('IPC main class level', ['icml'], '') },
            { id: 'icsl', text: cql_field_chooser_text('IPC secondary class level', ['icsl'], '') },
            { id: 'ical', text: cql_field_chooser_text('IPC additional class level', ['ical'], '') },
        ],
    },
    {
        text: '<h4>Reclassified IPC</h4>',
        children: [
            { id: 'mcd', text: cql_field_chooser_text('Reclassified IPC', ['mcd'], '') },
            { id: 'mcm', text: cql_field_chooser_text('MCD main class', ['mcm'], '') },
            { id: 'mcs', text: cql_field_chooser_text('MCD secondary class', ['mcs'], '') },
            { id: 'mca', text: cql_field_chooser_text('MCD additional class', ['mca'], '') },
            { id: 'mcml', text: cql_field_chooser_text('MCD main class level', ['mcml'], '') },
            { id: 'mcsl', text: cql_field_chooser_text('MCD secondary class level', ['mcsl'], '') },
            { id: 'mcal', text: cql_field_chooser_text('MCD additional class level', ['mcal'], '') },
        ],
    },
    {
        text: '<h4>Search file IPC</h4>',
        children: [
            { id: 'icp', text: cql_field_chooser_text('Search file IPC', ['icp'], '') },
        ],
    },
];
