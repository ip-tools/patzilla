// -*- coding: utf-8 -*-
// (c) 2013,2014 Andreas Motl, Elmyra UG

// this must be rendered inline to get rid of monster url parameters as early as possible

function param_regex(name) {
    // https://stackoverflow.com/questions/1842681/regular-expression-to-remove-one-parameter-from-query-string
    return new RegExp('&' + name + '\=([^&]*)?(?=&|$)|' + name + '\=([^&]*)?(&|$)');
}
function strip_param(url, name) {
    return url.replace(param_regex(name), '');
}
function get_param(url, name) {
    var m = url.match(param_regex(name));
    if (m) return m[1];
}

// Transfer "database=" query parameter to temporary location
// and clear from url to avoid referrer spam
var url = url_clean = window.location.search;
var database = get_param(url, 'database');
if (database) {
    window.request_hidden = {database: decodeURIComponent(database)};
    url_clean = strip_param(url_clean, 'database');
}

// Clear "op=" query parameter
url_clean = strip_param(url_clean, 'op');

// Reset url
if (url_clean != url) {
    history.pushState({id: 'url-clean'}, '', url_clean);
}
