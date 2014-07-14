// -*- coding: utf-8 -*-
// (c) 2013,2014 Andreas Motl, Elmyra UG

function to_list(value) {
    return _.isArray(value) && value || [value];
}

function now_iso() {
    return moment().format();
}
timestamp = now_iso;

function now_iso_human() {
    return moment().format('YYYY-MM-DD HH:mm:ss');
}

function today_iso() {
    return moment().format('YYYY-MM-DD');
}

function changeTooltipColorTo(color) {
    $('.tooltip-inner').css('background-color', color)
    $('.tooltip.top .tooltip-arrow').css('border-top-color', color);
    $('.tooltip.right .tooltip-arrow').css('border-right-color', color);
    $('.tooltip.left .tooltip-arrow').css('border-left-color', color);
    $('.tooltip.bottom .tooltip-arrow').css('border-bottom-color', color);
}

function quotate(value) {
    // TODO: use _.string.surround(str, wrapper)
    return '"' + value + '"';
}

// http://stackoverflow.com/questions/263965/how-can-i-convert-a-string-to-boolean-in-javascript/21976486#21976486
function asbool(value) {
    if (typeof(value) == 'string') {
        value = value.trim().toLowerCase();
    }
    switch(value){
        case true:
        case "true":
        case 1:
        case "1":
        case "on":
        case "yes":
            return true;
        default:
            return false;
    }
}

// http://stackoverflow.com/questions/5538972/console-log-apply-not-working-in-ie9/5539378#5539378
if (Function.prototype.bind) {
    var log = Function.prototype.bind.call(console.log, console);
} else {
    var log = function() {};
}

// http://stackoverflow.com/questions/572604/javascript-how-to-extend-array-prototype-push/572631#572631
_.clear = function(array) {
    array.length = 0;
};

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

// http://stackoverflow.com/questions/3344392/dynamic-deep-selection-for-a-javascript-object/3344487#3344487
function dotresolve(cur, ns) {
    var undef;
    ns = ns.split('.');
    while (cur && ns[0])
        cur = cur[ns.shift()] || undefined;
    return cur;
}

// https://gist.github.com/eethann/3430971
// Underscore mixin with common iterator functions adapted to work with objects and maintain key/val pairs
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

function deferreds_bundle(deferreds) {
    // wait for all add operations to finish before signalling success
    var deferred = $.Deferred();
    $.when.apply($, deferreds).then(function() {
        deferred.resolve();
    });
    return deferred.promise();
}
