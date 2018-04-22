// -*- coding: utf-8 -*-
// (c) 2013-2017 Andreas Motl, Elmyra UG

// strip patent kindcode for the poorest
function patent_number_strip_kindcode(patent_number) {
    var re = /.+\d+(\D)/g;
    var match = re.exec(patent_number);
    if (match && match[1]) {
        var position = re.lastIndex;
        if (position) {
            patent_number = patent_number.substring(0, position - 1);
        }
    }
    return patent_number;
}

// Derived from patzilla.util.numbers.common.
// Also handles DE000B0012324MAZ, IN2012KN00054A.
var patent_number_pattern = /^(\D\D)(\d*\D{0,2}[\d.]+?)([a-zA-Z].{0,2})?(_.+)?$/;
var patent_number_pattern_groups = ['country', 'number', 'kind', 'ext'];
function split_patent_number(patent_number) {

    var patent = {};

    var match = patent_number_pattern.exec(patent_number);
    if (!match) { return patent; }

    _.each(patent_number_pattern_groups, function(matchname, index) {
        var match_index = index + 1;
        try {
            patent[matchname] = match[match_index] || '';
        } catch (ex) {
            patent[matchname] = '';
        }
    });

    return patent;

}

function normalize_numberlist(payload) {
    var deferred = $.Deferred();
    $.ajax({
            method: 'post',
            url: '/api/util/numberlist?normalize=true',
            beforeSend: function(xhr, settings) {
                xhr.requestUrl = settings.url;
            },
            data: payload,
            contentType: "text/plain; charset=utf-8",
        }).then(function(response, status, options) {
            if (response) {
                deferred.resolve(response);
            } else {
                navigatorApp.ui.notify('Number normalization failed (empty response)', {type: 'warning', icon: 'icon-exchange', right: true});
                deferred.reject();
            }
        }).catch(function(xhr, settings) {
            console.warn('Error with normalize_numberlist:', xhr);
            navigatorApp.ui.propagate_backend_errors(xhr);
            deferred.reject();
        });
    return deferred.promise();
}

exports.patent_number_strip_kindcode = patent_number_strip_kindcode;
exports.normalize_numberlist = normalize_numberlist;
exports.split_patent_number = split_patent_number;
