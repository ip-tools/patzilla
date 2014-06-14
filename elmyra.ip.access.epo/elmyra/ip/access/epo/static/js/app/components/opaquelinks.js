// -*- coding: utf-8 -*-
// (c) 2014 Andreas Motl, Elmyra UG

// generate opaque token from parameter object
function opaquetoken(params) {
    var deferred = $.Deferred();
    $.ajax({
        method: 'post',
        url: '/api/opaquelinks/token',
        async: false,
        sync: true,
        data: JSON.stringify(params),
        contentType: "application/json; charset=utf-8",
    }).success(function(payload) {
        if (payload) {
            deferred.resolve(payload);
        }
    }).error(function(error) {
        console.warn('Error while signing opaque parameters', error);
        deferred.reject(error);
    });
    return deferred.promise();
}

// generate url with opaque token from parameter object
function opaqueurl(params) {
    var deferred = $.Deferred();
    opaquetoken(params).then(function(token) {
        var liveview_url = '?op=' + token;
        deferred.resolve(liveview_url);
    });
    return deferred.promise();
}
