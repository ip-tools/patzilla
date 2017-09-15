// -*- coding: utf-8 -*-
// (c) 2013-2017 Andreas Motl, Elmyra UG
require('jquery');
require('underscore');
require('underscore.string');


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
                    .filter(':first').click();
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


// ------------------------------------------
//   Addons to Underscore.js 1.4.4
// ------------------------------------------

// TODO: We are already on Underscore.js 1.8.3. Check these addons!

// http://stackoverflow.com/questions/572604/javascript-how-to-extend-array-prototype-push/572631#572631
_.clear = function(array) {
    array.length = 0;
};

/*
 _.move - takes array and moves item at index and moves to another index; great for use with jQuery.sortable()
 https://gist.github.com/kjantzer/3974823
 */
_.mixin({
    move: function(array, fromIndex, toIndex) {
        array.splice(toIndex, 0, array.splice(fromIndex, 1)[0]);
        return array;
    }
});


// Underscore mixins with common iterator functions adapted to work with objects and maintain key/val pairs
// https://gist.github.com/eethann/3430971
_.mixin({
    // ### _.objMap
    // _.map for objects, keeps key/value associations
    objMap: function (input, mapper, context) {
        return _.reduce(input, function (obj, v, k) {
            obj[k] = mapper.call(context, v, k, input);
            return obj;
        }, {}, context);
    },
    // ### _.objFilter
    // _.filter for objects, keeps key/value associations
    // but only includes the properties that pass test().
    objFilter: function (input, test, context) {
        return _.reduce(input, function (obj, v, k) {
            if (test.call(context, v, k, input)) {
                obj[k] = v;
            }
            return obj;
        }, {}, context);
    },
    // ### _.objReject
    //
    // _.reject for objects, keeps key/value associations
    // but does not include the properties that pass test().
    objReject: function (input, test, context) {
        return _.reduce(input, function (obj, v, k) {
            if (!test.call(context, v, k, input)) {
                obj[k] = v;
            }
            return obj;
        }, {}, context);
    },
    // ### _.objRejectEmpty
    //
    // reject all items with empty values
    objRejectEmpty: function(input) {
        return _.objReject(input, function(value, key) {
            return _.isEmpty(value);
        });
    },
});

// Underscore mixins to sort object keys.
// Like _.sortBy(), but on keys instead of values, returning an object, not an array. Defaults to alphanumeric sort.
// https://gist.github.com/colingourlay/82506396503c05e2bb94
_.mixin({
    'sortKeysBy': function (obj, comparator) {
        var keys = _.sortBy(_.keys(obj), function (key) {
            return comparator ? comparator(obj[key], key) : key;
        });

        return _.object(keys, _.map(keys, function (key) {
            return obj[key];
        }));
    }
});
