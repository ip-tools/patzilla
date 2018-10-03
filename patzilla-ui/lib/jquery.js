// -*- coding: utf-8 -*-
// (c) 2013-2018 Andreas Motl <andreas.motl@ip-tools.org>

// jQuery fame
require('jquery');

// Helper for transitioning to jQuery 3.x
// https://www.npmjs.com/package/jquery-migrate
require('jquery-migrate');



// ------------------------------------------
//   Addons to jQuery 3.3.1
// ------------------------------------------


// Global exception handlers

// https://www.learningjquery.com/2017/03/different-methods-of-error-handling-in-jquery
/*
jQuery.readyException = function(error) {
    console.error('jQuery exception:', error);
    throw error;
};
*/


// ------------------------------------------
//   Addons to jQuery 1.9.1
// ------------------------------------------

// TODO: We are already on jQuery 1.12.4. Check these addons!

// qnotify
(function($) {
    $.fn.extend({
        qnotify: function(message, options) {
            options = options || {};
            _.defaults(options, {className: 'info', position: 'bottom'});
            if (options.error) options.className = 'error';
            if (options.success) options.className = 'success';
            if (options.warn || options.warning) options.className = 'warning';
            $(this).notify(message, options);
        },

    });
})(jQuery);

// .exists()
// https://stackoverflow.com/questions/920236/how-can-i-detect-if-a-selector-returns-null/920322#920322
$.fn.exists = function () {
    return this.length !== 0;
}

// https://stackoverflow.com/questions/964734/hitting-enter-does-not-post-form-in-ie8/4629047#4629047
// Recreating normal browser behavior in Javascript. Thank you, Microsoft.
// Same behaviour in Safari. :-)
jQuery.fn.handle_enter_keypress = function() {

    // https://stackoverflow.com/questions/9847580/how-to-detect-safari-chrome-ie-firefox-and-opera-browser/9851769#9851769

    // At least IE6
    var isInternetExplorer = /*@cc_on!@*/false || !!document.documentMode;

    // At least Safari 3+: "[object HTMLElementConstructor]"
    var isSafari = Object.prototype.toString.call(window.HTMLElement).indexOf('Constructor') > 0;

    if (isInternetExplorer || isSafari) {
        $(this).find('input').keypress(function(e) {
            // If the key pressed was enter
            if (e.which == '13') {
                $(this).closest('form')
                    .find('button[type=submit],input[type=submit]')
                    .filter(':first').trigger('click');
            }
        });
    }
}

// .toggleCheck()
// https://stackoverflow.com/questions/4177159/toggle-checkboxes-on-off/18268117#18268117
$.fn.toggleCheck = function() {
    if (!$(this).exists()) {
        return;
    }

    var element = this[0];
    if (element.tagName === 'INPUT') {
        $(element).prop('checked', !($(element).prop('checked')));
    }
}
