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
function opaquetoken_query(params) {
    var deferred = $.Deferred();
    opaquetoken(params).then(function(token) {
        var query_part = 'op=' + token;
        deferred.resolve(query_part);
    });
    return deferred.promise();
}

function opaque_param(params) {
    // serialize state into opaque parameter token
    // TODO: make this idempotent by saving the original "href" contents into a "data" attribute
    // if we can reperform the token generation on each click, liveview documents will live forever
    // i.e. can always spawn liveview links with valid tokens; OTOH, think about the implications first

    params = params || {};

    // skip if "op" is already in url
    var url = $.url(href);
    if (params['op']) {
        return $.Deferred().resolve('op=' + params['op']);
    }

    // sign parameters, generate JWT token and opaque parameter url
    return opaquetoken_query(params);

}
