// -*- coding: utf-8 -*-
// (c) 2014-2016 Andreas Motl, Elmyra UG
require('jquery');
require('jrumble');
require('purl/purl');
require('bootstrap-2.3.2/css/bootstrap.css');
require('bootstrap-2.3.2/css/bootstrap-responsive.css');
require('fontawesome-3.2.1/css/font-awesome.css');
require('patzilla.navigator.style');

$(document).ready(function() {
    console.log("document.ready");

    var url = $.url(window.location.href);
    var domain = url.attr('host');

    $.extend(login_settings, {domain: domain});

    if (url.param('error') == 'true') {
        console.warn('Login failed. Please check your credentials or contact us for support at ' + login_settings.support_email + '.');
        window.setTimeout(function() {
            $('.login-box').jrumble();
            $('.login-box').trigger('startRumble');
            window.setTimeout(function() {
                $('.login-box').trigger('stopRumble');
            }, 333);
        }, 150);
    }

    $('#mail-register').unbind('click');
    $('#mail-register').bind('click', function() {

        var subject = _.template('<%= productname %>: Account registration on domain "<%= domain %>"')(login_settings);
        var body = _.template(_.string.ltrim($('#template-mail-register').html()))(login_settings);

        tweak_mailto(this, subject, body);

    });

    $('#mail-login-failed').unbind('click');
    $('#mail-login-failed').bind('click', function() {

        var subject = _.template('<%= productname %>: Login keeps failing for account "<%= username %>" on domain "<%= domain %>"')(login_settings);
        var body = _.template(_.string.ltrim($('#template-mail-login-failed').html()))(login_settings);

        tweak_mailto(this, subject, body);

    });

    $('#visit-demo').unbind('click');
    $('#visit-demo').bind('click', function() {

        var demourl = url.attr('protocol') + '://' + url.attr('host');
        if (url.attr('port')) demourl += ':' + url.attr('port');
        if (_.string.contains(demourl, 'patentsearch')) {
            demourl = demourl.replace('patentsearch', 'patentview');
        } else if (_.string.contains(demourl, 'ip-tools.io')) {
            demourl = demourl.replace(url.attr('host'), 'patentview.ip-tools.io');
        }
        demourl += '?op=eyJhbGciOiAiUFMyNTYiLCAidHlwIjogIkpXVCJ9.eyJqdGkiOiAiUmlnSGlLRm91N0daUlVseDdTTTBYRkNXdWlqOUlLNnFoaS1lUnowMUdVOEVqVzFUb1lrWHRGLXdFekJqbTA5WjA3bndmN0JtZmJfcnFfeC1xcUd4Qm5qRl9CN0Zkb1NCOTJoZ25DNXg2aDA2OVBiZGtwRjlKdUhRUzVoZ0RLY212M2VPenFQOVlVTlBqTmdpaGM0Rmo3U25OMHJiS3ExRTByN2EweVk3N19rPSIsICJkYXRhIjogeyJwcm9qZWN0IjogInF1ZXJ5LXBlcm1hbGluayIsICJxdWVyeSI6ICJCaT0oKEdyZWlmZT8gT1IgR3JpcD8pIGFuZCAocm9ociBvciB0dWJlIG9yIGNpcmN1bGFyKSkgYW5kIHBjPShERSBvciBFUCkgYW5kIElDPShCMjZEPyBvciBCMjNEPykiLCAibW9kZSI6ICJsaXZldmlldyIsICJjb250ZXh0IjogInZpZXdlciIsICJkYXRhc291cmNlIjogImRlcGF0aXNuZXQifSwgIm5iZiI6IDE0MDU1MjcwMjMsICJleHAiOiAxNTYxMDQ3MDIzLCAiaWF0IjogMTQwNTUyNzAyM30.Ec0CjI2lLPLAoVxADDrkZlIRgbELqfUAP-0kKtrnWZ6YIm9iUc-KhekqWigyLQ-cSVWCDymLorON-KN79xojgzCvV8D-FZTwXVjMOwREGUJ6osm-7NiCNhXIjDCh1H2X';

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
