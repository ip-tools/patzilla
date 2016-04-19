// -*- coding: utf-8 -*-
// (c) 2013,2014 Andreas Motl, Elmyra UG

function _field_text(label, fields, more, options) {

    // short-circuit enrichment
    //return label;

    fields = to_list(fields);
    options = options || {};

    _.defaults(options, {'sep': '='});
    var separator = options.sep;

    var tpl = _.template($('#cql-field-chooser-entry').html());
    fields = fields.map(function(item) { return item + separator });
    var html = tpl({label: label, fields: fields, more: more});
    return html;
}

function _field_text_ifi(label, fields, more, options) {
    options = options || {};
    options.sep = ':';
    return _field_text(label, fields, more, options);
}

var OPS_CQL_FIELDS = [
    {
        text: '<h4>Popular</h4>',
        children: [
            { id: 'num', text: _field_text('Publication-, application- or<br/>priority number', ['num'], '(10, 11, 21, 31)') },
            { id: 'txt', text: _field_text('Title, abstract, inventor-, or applicant name', ['txt'], '(54, 57, 72, 71, 73)') },
            { id: 'cl', text: _field_text('CPC or IPC8 class', ['cl'], '') },
        ],
    },
    {
        text: '<h4>Publication</h4>',
        children: [
            { id: 'pn', text: _field_text('Publication number', ['pn', 'publicationnumber'], '(10, 11)') },
            { id: 'pd', text: _field_text('Publication date', ['pd', 'publicationdate'], '(40)') },
            { id: 'pa', text: _field_text('Applicant', ['pa', 'applicant'], '(71, 73)') },
            { id: 'in', text: _field_text('Inventor', ['in', 'inventor'], '(72)') },
            { id: 'ia', text: _field_text('Inventor or applicant', ['ia', 'inventorandapplicant'], '(72, 71, 73)') },
            { id: 'spn', text: _field_text('Publication number<br/><small>in epodoc format</small>', ['spn'], '') },
        ],
    },
    {
        text: '<h4>Text</h4>',
        children: [
            { id: 'ti', text: _field_text('Title', ['ti', 'title'], '(54)') },
            { id: 'ab', text: _field_text('Abstract', ['ab', 'abstract'], '(57)') },
            { id: 'ta', text: _field_text('Title or abstract', ['ta', 'titleandabstract'], '(54, 57)') },
            { id: 'txt', text: _field_text('Title, abstract, inventor-, or applicant name', ['txt'], '(54, 57, 72, 71, 73)') },
        ],
    },
    {
        text: '<h4>Application, priority and family</h4>',
        children: [
            { id: 'ap', text: _field_text('Application number', ['ap', 'applicantnumber'], '(21)') },
            { id: 'sap', text: _field_text('Application number<br/><small>in epodoc format</small>', ['sap'], '') },
            { id: 'pr', text: _field_text('Priority number', ['pr', 'prioritynumber'], '(31)') },
            { id: 'spr', text: _field_text('Priority number<br/><small>in epodoc format</small>', ['spr'], '') },
            { id: 'famn', text: _field_text('Family identifier (simple)', ['famn'], '') },
        ],
    },
    {
        text: '<h4>Classification</h4>',
        children: [
            { id: 'cpc', text: _field_text('CPC classification<br/><small>(invention and additional)</small>', ['cpc', 'cpci', 'cpca'], '') },
            { id: 'ipc', text: _field_text('IPC8 class', ['ipc', 'ic'], '') },
            { id: 'ci', text: _field_text('IPC8 core invention class', ['ci'], '') },
            { id: 'cn', text: _field_text('IPC8 core additional class<br/><small>(non-invention)</small>', ['cn'], '') },
            { id: 'ai', text: _field_text('IPC8 advanced invention class', ['ai'], '') },
            { id: 'an', text: _field_text('IPC8 advanced additional class<br/><small>(non-invention)</small>', ['an'], '') },
            { id: 'a', text: _field_text('IPC8 advanced class', ['a'], '') },
            { id: 'c', text: _field_text('IPC8 core class', ['c'], '') },
            { id: 'cl', text: _field_text('CPC or IPC8 class', ['cl'], '') },
        ],
    },
    {
        text: '<h4>Citations</h4>',
        children: [
            { id: 'ct', text: _field_text('Cited document number', ['ct', 'citation'], '(56)') },
            { id: 'ex', text: _field_text('Cited document number<br/><small>during examination</small>', ['ex'], '') },
            { id: 'op', text: _field_text('Cited document number<br/><small>during opposition</small>', ['op'], '') },
            { id: 'rf', text: _field_text('Cited document number<br/><small>provided by applicant</small>', ['rf'], '') },
            { id: 'oc', text: _field_text('Another cited document number', ['oc'], '') },
        ],
    },
];

var DEPATISNET_CQL_FIELDS = [
    {
        text: '<h4>Publication</h4>',
        children: [
            { id: 'pn', text: _field_text('Publication number', ['pn'], '(10, 11)') },
            { id: 'pc', text: _field_text('Country of publication', ['pc'], '(19)') },
            { id: 'pub', text: _field_text('Publication date', ['pub'], '(40)') },
            { id: 'py', text: _field_text('Publication year', ['py'], '(40)') },
            { id: 'pa', text: _field_text('Applicant/Owner', ['pa'], '(71, 73)') },
            { id: 'in', text: _field_text('Inventor', ['in'], '(72)') },
            { id: 'pcod', text: _field_text('Kind code', ['pcod'], '(12)') },
        ],
    },
    {
        text: '<h4>Text</h4>',
        children: [
            { id: 'ti', text: _field_text('Title', ['ti'], '(54)') },
            { id: 'ab', text: _field_text('Abstract', ['ab'], '(57)') },
            { id: 'de', text: _field_text('Description', ['de'], '') },
            { id: 'cl', text: _field_text('Claims', ['cl'], '(57)') },
            { id: 'bi', text: _field_text('Full text data', ['bi']) },
        ],
    },
    {
        text: '<h4>Application</h4>',
        children: [
            { id: 'an', text: _field_text('Application number', ['ap'], '(21)') },
            { id: 'ac', text: _field_text('Country of application', ['ac'], '') },
            { id: 'ad', text: _field_text('Application date', ['ad'], '(22, 96)') },
            { id: 'ay', text: _field_text('Application year', ['ay'], '') },
        ],
    },
    {
        text: '<h4>Priority</h4>',
        children: [
            { id: 'prn', text: _field_text('Priority number', ['prn'], '(31)') },
            { id: 'prc', text: _field_text('Country of priority', ['prc'], '(33)') },
            { id: 'prd', text: _field_text('Priority date', ['prd'], '(32)') },
            { id: 'pry', text: _field_text('Priority year', ['pry'], '') },
        ],
    },
    {
        text: '<h4>Citations</h4>',
        children: [
            { id: 'ct', text: _field_text('Cited documents', ['ct'], '(56)') },
            { id: 'ctnp', text: _field_text('Cited non-patent literature', ['ctnp'], '(56)') },
        ],
    },
    {
        text: '<h4>All IPC</h4>',
        children: [
            { id: 'ic', text: _field_text('All IPC fields', ['ic'], '') },
        ],
    },
    {
        text: '<h4>Bibliographic IPC</h4>',
        children: [
            { id: 'icb', text: _field_text('Bibliographic IPC', ['icb'], '') },
            { id: 'icm', text: _field_text('IPC main class', ['icm'], '(51)') },
            { id: 'ics', text: _field_text('IPC secondary class', ['ics'], '(51)') },
            { id: 'ica', text: _field_text('IPC additional class', ['ica'], '') },
            { id: 'ici', text: _field_text('IPC index classes', ['ici'], '') },
            { id: 'icmv', text: _field_text('IPC main class version', ['icmv'], '') },
            { id: 'icsv', text: _field_text('IPC secondary class version', ['icsv'], '') },
            { id: 'icav', text: _field_text('IPC additional class version', ['icav'], '') },
            { id: 'icml', text: _field_text('IPC main class level', ['icml'], '') },
            { id: 'icsl', text: _field_text('IPC secondary class level', ['icsl'], '') },
            { id: 'ical', text: _field_text('IPC additional class level', ['ical'], '') },
        ],
    },
    {
        text: '<h4>Reclassified IPC</h4>',
        children: [
            { id: 'mcd', text: _field_text('Reclassified IPC', ['mcd'], '') },
            { id: 'mcm', text: _field_text('MCD main class', ['mcm'], '') },
            { id: 'mcs', text: _field_text('MCD secondary class', ['mcs'], '') },
            { id: 'mca', text: _field_text('MCD additional class', ['mca'], '') },
            { id: 'mcml', text: _field_text('MCD main class level', ['mcml'], '') },
            { id: 'mcsl', text: _field_text('MCD secondary class level', ['mcsl'], '') },
            { id: 'mcal', text: _field_text('MCD additional class level', ['mcal'], '') },
        ],
    },
    {
        text: '<h4>Search file IPC</h4>',
        children: [
            { id: 'icp', text: _field_text('Search file IPC', ['icp'], '') },
        ],
    },
];

var DEPATISNET_SORT_FIELDS = [
    { id: 'pd', text: 'Publication date' },
    { id: 'vn', text: 'Publication number' },
    { id: 'in', text: 'Inventor' },
    { id: 'pa', text: 'Applicant' },
    { id: 'ti', text: 'Title' },
    { id: 'ad', text: 'Application date' },
    { id: 'icm', text: 'IPC main class' },
    { id: 'icsf', text: 'IPC secondary classes' },
    { id: 'mcsf', text: 'Reclassified IPC (MCD)' },
    { id: 'icp', text: 'Search file IPC' },
];

var IFI_CQL_FIELDS = [
    {
        text: '<h4>Popular</h4>',
        children: [
            { id: 'pn', text: _field_text_ifi('Publication identifier', 'pn', '(10, 11)') },
            { id: 'text', text: _field_text_ifi('Title, Abstract, Description, Claims', 'text', '(54, 57)') },
            { id: 'ic', text: _field_text_ifi('International classification', 'ic', '(51)') },
            { id: 'cpc', text: _field_text_ifi('CP Classification', 'cpc', '') },
        ],
    },
    {
        // Publication Information
        text: '<h4>Publication</h4>',
        children: [
            { id: 'pnlang', text: _field_text_ifi('Publication language', 'pnlang', '(26)') },
            { id: 'pd', text: _field_text_ifi('Publication date', 'pd', '(40)') },
        ],
    },
    {
        // Parties
        text: '<h4>Parties</h4>',
        children: [
            { id: 'pa',     text: _field_text_ifi('Applicants, Assignees', 'pa', '(71, 73)') },
            { id: 'inv',    text: _field_text_ifi('Inventors', 'inv', '(72)') },
            { id: 'apl',    text: _field_text_ifi('Applicants', 'apl', '(71)') },
            { id: 'asg',    text: _field_text_ifi('Assignees', 'asg', '(73)') },
            { id: 'reasg',  text: _field_text_ifi('Reassignees', 'reasg', '(73)') },
            { id: 'agt',    text: _field_text_ifi('Agents', 'agt', '(74)') },
            { id: 'cor',    text: _field_text_ifi('Correspondent name', 'cor', '') },
        ],
    },
    {
        // Text fields
        text: '<h4>Text</h4>',
        children: [
            { id: 'text',   text: _field_text_ifi('Title, Abstract, Description, Claims', 'text', '(54, 57)') },
            { id: 'tac',    text: _field_text_ifi('Title, Abstract, Claims', 'tac', '(54, 57)') },
            { id: 'ttl',    text: _field_text_ifi('Title', 'ttl', '(54)') },
            { id: 'ab',     text: _field_text_ifi('Abstract', 'ab', '(57)') },
            { id: 'desc',   text: _field_text_ifi('Description', 'desc', '(57)') },
            { id: 'clm',    text: _field_text_ifi('Claims', 'clm', '(57)') },
            { id: 'aclm',   text: _field_text_ifi('Amended claims', 'clm', '(57)') },
        ],
    },
    {
        // Classifications
        text: '<h4>Classifications</h4>',
        children: [
            { id: 'ic',     text: _field_text_ifi('International classification', 'ic', '(51)') },
            { id: 'cpc',    text: _field_text_ifi('CP classification', 'cpc', '') },
            { id: 'ecla',   text: _field_text_ifi('ECLA classification', 'ecla', '') },
            { id: 'uc',     text: _field_text_ifi('US classification', 'uc', '') },
            { id: 'fi',     text: _field_text_ifi('FI classification', 'fi', '') },
            { id: 'fterm',  text: _field_text_ifi('F-Terms', 'fterm', '') },
        ],
    },
    {
        text: '<h4>Filing/Application and priority</h4>',
        children: [
            // Filing Information
            { id: 'an',     text: _field_text_ifi('Filing identifier', 'an', '(21)') },
            { id: 'anlang', text: _field_text_ifi('Filing language', 'anlang', '(25)') },
            { id: 'ad',     text: _field_text_ifi('Filing date', 'ad', '(22)') },

            // Priority Filing Information
            { id: 'pri',    text: _field_text_ifi('Priority identifiers', 'pri', '(31)') },
            { id: 'pridate', text: _field_text_ifi('Priority dates', 'pridate', '(32)') },
            { id: 'regd',   text: _field_text_ifi('DE registration date', 'regd', '') },
        ],
    },
    {
        // International Filing and Publishing data
        text: '<h4>International Filing and Publishing data</h4>',
        children: [
            { id: 'pctan',  text: _field_text_ifi('PCT application identifier', 'pctan', '(86)') },
            { id: 'pctad',  text: _field_text_ifi('PCT application date', 'pctad', '(86)') },
            { id: 'pctpn',  text: _field_text_ifi('PCT publication identifier', 'pctpn', '(87)') },
            { id: 'pctpd',  text: _field_text_ifi('PCT publication date', 'pctpd', '(87)') },
            { id: 'ds',     text: _field_text_ifi('Designated states', 'ds', '(81)') },
        ],
    },
    {
        // Citations
        text: '<h4>Citations</h4>',
        children: [
            { id: 'pcit',   text: _field_text_ifi('Patent citations (full information)', 'pcit', '') },
            { id: 'pcitpn', text: _field_text_ifi('Patent citation identifier', 'pcitpn', '') },
            { id: 'ncit',   text: _field_text_ifi('Non-patent citations (full information)', 'ncit', '') },
        ],
    },
    {
        // Related Documents
        text: '<h4>Related Documents</h4>',
        children: [
            { id: 'relan',  text: _field_text_ifi('Related applications', 'relan', '') },
            { id: 'relad',  text: _field_text_ifi('Related applications date', 'relad', '') },
            { id: 'relpn',  text: _field_text_ifi('Related publications identifier', 'relpn', '') },
            { id: 'relpd',  text: _field_text_ifi('Related publications publication date', 'relpd', '') },
        ],
    },
    {
        // Legal Status Events
        text: '<h4>Legal Status Events</h4>',
        children: [
            { id: 'ls',     text: _field_text_ifi('Legal status: All legal status fields w/o lsconv, lsrf)', 'ls', '') },
            { id: 'lsconv', text: _field_text_ifi('Legal status conveyance', 'lsconv', '') },
            { id: 'lsrf',   text: _field_text_ifi('Legal status reel-frame', 'lsrf', '') },
            { id: 'lstext', text: _field_text_ifi('Legal status text', 'lstext', '') },
        ],
    },
    {
        text: '<h4>Miscellaneous</h4>',
        children: [
            { id: 'fam',    text: _field_text('Family identifier', 'fam', '') },
        ],
    },
];


var FIELDS_KNOWLEDGE = {
    'ops': {
        'meta': {
            'separator': '=',
        },
        'fields': OPS_CQL_FIELDS,
    },
    'depatisnet': {
        'meta': {
            'separator': '=',
        },
        'fields': DEPATISNET_CQL_FIELDS,
        'sorting': DEPATISNET_SORT_FIELDS,
    },
    'ifi': {
        'meta': {
            'separator': ':',
        },
        'fields': IFI_CQL_FIELDS,
    },
};
