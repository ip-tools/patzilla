// -*- coding: utf-8 -*-
// (c) 2013,2014 Andreas Motl, Elmyra UG

// this must be rendered inline to get rid of monster url parameters as early as possible

function uc_param_regex(name) {
    // https://stackoverflow.com/questions/1842681/regular-expression-to-remove-one-parameter-from-query-string
    return new RegExp('.*' + name + '=(.+?)(&|$)');
}
function uc_strip_param(url, name) {
    return url.replace(uc_param_regex(name), '');
}
function uc_get_param(url, name) {
    var m = url.match(uc_param_regex(name));
    if (m) return m[1];
}

// Transfer "database=" query parameter to temporary location
// and clear from url to avoid referrer spam
var url = url_clean = window.location.search;
var database = uc_get_param(url, 'database');
if (database) {
    window.request_hidden = {database: decodeURIComponent(database)};
    url_clean = uc_strip_param(url_clean, 'database');
}

// Clear "op=" query parameter when too long
var op = uc_get_param(url, 'op');
if (op && op.length > 1400) {
    url_clean = uc_strip_param(url_clean, 'op');
}

// Reset url
if (url_clean != url) {
    if (url_clean == '') {
        url_clean = '?';
    }
    history.replaceState({id: 'url-clean'}, '', url_clean);
}
