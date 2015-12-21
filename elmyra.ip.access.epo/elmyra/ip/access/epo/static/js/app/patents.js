// -*- coding: utf-8 -*-
// (c) 2013-2015 Andreas Motl, Elmyra UG

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

// derived from elmyra.ip.util.numbers.common
var patent_number_pattern = /^(\D\D)(0*\D{0,2}[\d.]+?)([a-zA-Z].?)?(_.+)?$/;
var patent_number_pattern_groups = ['country', 'number', 'kind', 'ext'];
function split_patent_number(patent_number) {

    var patent = {};

    var match = patent_number_pattern.exec(patent_number);

    _.each(patent_number_pattern_groups, function(matchname, index) {
        var match_index = index + 1;
        patent[matchname] = match[match_index] || '';
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
    }).success(function(response, status, options) {
            if (response) {
                deferred.resolve(response);
            } else {
                opsChooserApp.ui.notify('Number normalization failed (empty response)', {type: 'warning', icon: 'icon-exchange', right: true});
                deferred.reject();
            }
        }).error(function(xhr, settings) {
            opsChooserApp.ui.propagate_alerts(xhr);
            deferred.reject();
        });
    return deferred.promise();
}
