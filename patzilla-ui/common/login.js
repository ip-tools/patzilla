// -*- coding: utf-8 -*-
// (c) 2014-2016 Andreas Motl, Elmyra UG
require('jquery');
require('jrumble');
require('purl/purl');
require('bootstrap-2.3.2/css/bootstrap.css');
require('bootstrap-2.3.2/css/bootstrap-responsive.css');
// Font Awesome 3.2.1; TODO: Upgrade to more recent version
require('font-awesome/css/font-awesome.css');
require('patzilla.navigator.style');

$(document).ready(function() {
    console.log("document.ready");

    var url = $.url(window.location.href);
    var domain = url.attr('host');

    $.extend(login_settings, {domain: domain});

    if (url.param('error') == 'true') {
        console.warn('Login failed (reason=' + url.param('reason') + '). Please check your credentials or contact us for support at ' + login_settings.support_email + '.');
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

        var demourl = url.attr('protocol') + '://' + url.attr('host');
        if (url.attr('port')) demourl += ':' + url.attr('port');
        if (_.string.contains(demourl, 'patentsearch')) {
            demourl = demourl.replace('patentsearch', 'patentview');
        } else if (_.string.contains(demourl, 'navigator')) {
            demourl = demourl.replace('navigator', 'viewer');
        } else if (_.string.contains(demourl, 'patbib')) {
            demourl = demourl.replace('patbib', 'patview');
        } else if (!_.string.contains(demourl, 'localhost')) {
            demourl = demourl.replace(url.attr('host'), 'patentview.ip-tools.io');
        }
        demourl += '?op=eyJhbGciOiAiUlMyNTYiLCAidHlwIjogIkpXVCJ9.eyJqdGkiOiAiZDZUT3Ewc3NkRDB6TTVCSGdhOEJrQT09IiwgImRhdGEiOiB7InByb2plY3QiOiAicXVlcnktcGVybWFsaW5rIiwgInF1ZXJ5IjogInR4dD0oU1M3IG9yICh0ZWxlY29tbXVuaWNhdGlvbiBvciBjb21tdW5pY2F0aW9uIG9yIGNvbXVuaWNhY2lcdTAwZjNuKSBvciAobW9iaWxlIG9yIE1vYmlsZnVua25ldHopIG9yIChuZXR3b3JrIG9yIChzZWN1cml0eSBvciBTaWNoZXJ1bmcpKSkgYW5kIHBhPShtb2JpbCBvciBrb21tdW5pa2F0aW9uKSBhbmQgY2w9KEgwNFcxMi8xMiBvciBIMDRMNjMvMDI4MSBvciBIMDRMNjMvMDQxNCkgbm90IHBuPShDTiBvciBDQSBvciBKUCkiLCAibW9kZSI6ICJsaXZldmlldyIsICJjb250ZXh0IjogInZpZXdlciIsICJkYXRhc291cmNlIjogIm9wcyJ9LCAibmJmIjogMTUwNzgyNjYxNywgImV4cCI6IDE2NjMzNDY2MTcsICJpYXQiOiAxNTA3ODI2NjE3fQ.fCl7I5wPd0r48O48UkVQxzw9QOy5PjFaFecmAoYisbM-Her9Z6R0E2hxc82TSdH68gz379jQe5v9eF6g620aG4odTOXtdhyoDrWcb-GJcfR-0BfpiqPRwzLng53ape69';

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
