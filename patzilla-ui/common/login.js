// -*- coding: utf-8 -*-
// (c) 2014-2016 Andreas Motl, Elmyra UG
require('jquery');
require('jrumble');
require('patzilla.lib.bootstrap');
require('patzilla.navigator.style');

$(function() {
    console.log("document.ready");

    var url = URL.parse(window.location.href);
    var domain = url.hostname;

    $.extend(login_settings, {domain: domain});

    $('.login-modal').modal({backdrop: 'static'});

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

    $('#form-magic-link').off('submit');
    $('#form-magic-link').on('submit', function(event) {
        event.preventDefault();

        var $email = $('#magic-link-email');
        var $cameFrom = $('#magic-link-came-from');
        var $submit = $('#magic-link-submit');
        var $feedback = $('#magic-link-feedback');

        var email = ($email.val() || '').trim();
        var cameFrom = ($cameFrom.val() || '').trim();

        $feedback.addClass('d-none').removeClass('alert-success alert-danger').text('');
        $submit.prop('disabled', true);

        fetch('/api/identity/magic-link', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            body: JSON.stringify({
                email: email,
                came_from: cameFrom,
            }),
        })
        .then(function(response) {
            return response.json().then(function(data) {
                return { ok: response.ok, data: data };
            });
        })
        .then(function(result) {
            if (result.ok) {
                var message = (result.data && result.data.message)
                    || 'If the email address is valid, a sign-in link has been sent.';
                $feedback.removeClass('d-none').addClass('alert-success').text(message);
            } else {
                var errMsg = 'Could not send sign-in link. Please try again.';
                if (result.data && result.data.errors && result.data.errors.length > 0) {
                    errMsg = result.data.errors[0].description || errMsg;
                }
                $feedback.removeClass('d-none').addClass('alert-danger').text(errMsg);
            }
        })
        .catch(function() {
            $feedback.removeClass('d-none').addClass('alert-danger')
                .text('Network error while requesting sign-in link. Please try again.');
        })
        .finally(function() {
            $submit.prop('disabled', false);
        });
    });

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
