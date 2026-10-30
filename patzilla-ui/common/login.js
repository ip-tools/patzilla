// -*- coding: utf-8 -*-
// (c) 2014-2016 Andreas Motl, Elmyra UG
require('jquery');
require('jrumble');
require('bootstrap/dist/css/bootstrap.min.css');
// Font Awesome 3.2.1; TODO: Upgrade to more recent version
require('font-awesome/css/font-awesome.css');
require('patzilla.navigator.style');

$(document).ready(function() {
    console.log("document.ready");

    var url = URL.parse(window.location.href);
    var domain = url.hostname;

    $.extend(login_settings, {domain: domain});

    if (url.searchParams.get('error') == 'true') {
        console.warn('Login failed (reason=' + url.searchParams.get('reason') + '). Please check your credentials or contact us for support at ' + login_settings.support_email + '.');
        window.setTimeout(function() {
            $('.login-box').jrumble();
            $('.login-box').trigger('startRumble');
            window.setTimeout(function() {
                $('.login-box').trigger('stopRumble');
            }, 333);
        }, 150);
    }

    $('#mail-register').off('click');
    $('#mail-register').on('click', function() {

        var subject = _.template('<%= productname %>: Account registration on domain "<%= domain %>"')(login_settings);
        var body = _.template(_.string.ltrim($('#template-mail-register').html()))(login_settings);

        tweak_mailto(this, subject, body);

    });

    $('#mail-login-failed').off('click');
    $('#mail-login-failed').on('click', function() {

        var subject = _.template('<%= productname %>: Login keeps failing for account "<%= username %>" on domain "<%= domain %>"')(login_settings);
        var body = _.template(_.string.ltrim($('#template-mail-login-failed').html()))(login_settings);

        tweak_mailto(this, subject, body);

    });

    $('#visit-demo').off('click');
    $('#visit-demo').on('click', function() {

        var hostname = url.hostname;
        if (_.string.contains(hostname, 'patentsearch')) {
            hostname = hostname.replace('patentsearch', 'patentview');
        } else if (_.string.contains(hostname, 'navigator')) {
            hostname = hostname.replace('navigator', 'viewer');
        } else if (_.string.contains(hostname, 'patbib')) {
            hostname = hostname.replace('patbib', 'patview');
        } else if (!_.string.contains(hostname, 'localhost')) {
            hostname = hostname.replace(url.hostname, 'patentview.ip-tools.io');
        }

        var demourl = url.protocol + '//' + hostname;
        if (url.port) demourl += ':' + url.port;
        if (url.pathname) demourl += url.pathname.replace('login', '');
        demourl += '?op=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRhIjp7ImNvbnRleHQiOiJ2aWV3ZXIiLCJkYXRhc291cmNlIjoib3BzIiwibW9kZSI6ImxpdmV2aWV3IiwicHJvamVjdCI6InF1ZXJ5LXBlcm1hbGluayIsInF1ZXJ5IjoidHh0PSh3aW5kIGFuZCBlbmVyZ2llKSIsInR0bCI6IjE1Nzc2NjQwMCJ9LCJleHAiOjE5NTEwOTE5ODEsImlhdCI6MTc5MzMyNTU4MSwianRpIjoiRERtZ2d6ZU5TRFQ4Y3VzMG9vQVRLZyIsIm5iZiI6MTc5MzMyNTU4MX0.GNdX_sUHdx1lGwz-QejdyFQQyyIpVwr3naolrNJzTULNZm0QClfPmvyK-wpGpO6bp0DJYz2s8INJq-bNAkqBMgH8izyKiJ1VYFMVGE8jUNqT6X-wbWE_WnRevOhqwRCY';

        //console.log(demourl);
        $(this).attr('href', demourl);

    });

});

function tweak_mailto(element, subject, body) {

    // prevent double tweaking
    if ($(element).data('tweaked')) {
        return;
    }
    $(element).data('tweaked', true);

    var mailto_data = {
        'subject': subject,
        'body': body,
    };

    var href = $(element).attr('href');
    href += '?' + jQuery.param(mailto_data).replace(/\+/g, '%20');
    $(element).attr('href', href);
}
