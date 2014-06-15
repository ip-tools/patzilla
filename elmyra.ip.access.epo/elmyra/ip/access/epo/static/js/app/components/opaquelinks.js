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

function opaqueurl_amend(href, params) {

    params = params || {};

    // serialize state into opaque parameter token
    // TODO: make this idempotent by saving the original "href" contents into a "data" attribute
    // if we can reperform the token generation on each click, liveview documents will live forever
    // i.e. can always spawn liveview links with valid tokens; OTOH, think about the implications first
    var url = $.url(href);
    if (url.param('op')) {
        return $.Deferred().resolve(href);
    }

    // collect all vanilla url parameters
    // TODO: maybe just collect a deterministic list?
    _(params).extend(url.param());

    // sign parameters, generate JWT token and opaque parameter url
    return opaqueurl(params);

}
