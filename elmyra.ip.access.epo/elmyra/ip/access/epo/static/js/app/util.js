// -*- coding: utf-8 -*-
// (c) 2013-2015 Andreas Motl, Elmyra UG

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

function now_iso_filename() {
    return moment().format('YYYY-MM-DD_HH:mm:ss');
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

// ------------------------------------------
//   Addons to Underscore.js 1.4.4
// ------------------------------------------
// http://stackoverflow.com/questions/572604/javascript-how-to-extend-array-prototype-push/572631#572631
_.clear = function(array) {
    array.length = 0;
};

// _.findIndex was added in Underscore.js 1.8
// https://stackoverflow.com/questions/21631127/find-the-array-index-of-an-object-with-a-specific-key-value-in-underscore/24588304#24588304
var findIndex = function(arr, cond) {
    var i, x;
    for (i in arr) {
        x = arr[i];
        if (cond(x)) return parseInt(i);
    }
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


/*
 "Strip leading whitespace from each line in a string" by Sindre Sorhus
 https://github.com/sindresorhus/strip-indent/blob/master/index.js
 */
_.string.dedent = function(str) {
    const match = str.match(/^[ \t]*(?=\S)/gm);

    if (!match) {
        return str;
    }

    // Amendment: Dedent everything
    const re = new RegExp('^[ \\t]+', 'gm');
    return str.replace(re, '');
};


// ------------------------------------------
//   Addons to jQuery
// ------------------------------------------

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

// http://stackoverflow.com/questions/3344392/dynamic-deep-selection-for-a-javascript-object/3344487#3344487
function dotresolve(cur, ns) {
    var undef;
    ns = ns.split('.');
    while (cur && ns[0])
        cur = cur[ns.shift()] || undefined;
    return cur;
}

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


function deferreds_bundle(deferreds) {
    // wait for all add operations to finish before signalling success
    var deferred = $.Deferred();
    $.when.apply($, deferreds).then(function() {
        deferred.resolve();
    });
    return deferred.promise();
}

// http://phpjs.org/functions/htmlentities/
// https://github.com/kvz/phpjs/blob/master/functions/strings/htmlentities.js
function htmlentities(string, quote_style, charset, double_encode) {
    //  discuss at: http://phpjs.org/functions/htmlentities/
    // original by: Kevin van Zonneveld (http://kevin.vanzonneveld.net)
    //  revised by: Kevin van Zonneveld (http://kevin.vanzonneveld.net)
    //  revised by: Kevin van Zonneveld (http://kevin.vanzonneveld.net)
    // improved by: nobbler
    // improved by: Jack
    // improved by: Rafał Kukawski (http://blog.kukawski.pl)
    // improved by: Dj (http://phpjs.org/functions/htmlentities:425#comment_134018)
    // bugfixed by: Onno Marsman
    // bugfixed by: Brett Zamir (http://brett-zamir.me)
    //    input by: Ratheous
    //  depends on: get_html_translation_table
    //   example 1: htmlentities('Kevin & van Zonneveld');
    //   returns 1: 'Kevin &amp; van Zonneveld'
    //   example 2: htmlentities("foo'bar","ENT_QUOTES");
    //   returns 2: 'foo&#039;bar'

    var hash_map = get_html_translation_table('HTML_ENTITIES', quote_style),
        symbol = '';
    string = string == null ? '' : string + '';

    if (!hash_map) {
        return false;
    }

    if (quote_style && quote_style === 'ENT_QUOTES') {
        hash_map["'"] = '&#039;';
    }

    if ( !! double_encode || double_encode == null) {
        for (symbol in hash_map) {
            if (hash_map.hasOwnProperty(symbol)) {
                string = string.split(symbol)
                    .join(hash_map[symbol]);
            }
        }
    } else {
        string = string.replace(/([\s\S]*?)(&(?:#\d+|#x[\da-f]+|[a-zA-Z][\da-z]*);|$)/g, function (ignore, text, entity) {
            for (symbol in hash_map) {
                if (hash_map.hasOwnProperty(symbol)) {
                    text = text.split(symbol)
                        .join(hash_map[symbol]);
                }
            }

            return text + entity;
        });
    }

    return string;
}


function get_html_translation_table(table, quote_style) {
    //  discuss at: http://phpjs.org/functions/get_html_translation_table/
    // original by: Philip Peterson
    //  revised by: Kevin van Zonneveld (http://kevin.vanzonneveld.net)
    // bugfixed by: noname
    // bugfixed by: Alex
    // bugfixed by: Marco
    // bugfixed by: madipta
    // bugfixed by: Brett Zamir (http://brett-zamir.me)
    // bugfixed by: T.Wild
    // improved by: KELAN
    // improved by: Brett Zamir (http://brett-zamir.me)
    //    input by: Frank Forte
    //    input by: Ratheous
    //        note: It has been decided that we're not going to add global
    //        note: dependencies to php.js, meaning the constants are not
    //        note: real constants, but strings instead. Integers are also supported if someone
    //        note: chooses to create the constants themselves.
    //   example 1: get_html_translation_table('HTML_SPECIALCHARS');
    //   returns 1: {'"': '&quot;', '&': '&amp;', '<': '&lt;', '>': '&gt;'}

    // debugging
    //log('table, quote_style:', table, quote_style);

    var entities = {},
        hash_map = {},
        decimal;
    var constMappingTable = {},
        constMappingQuoteStyle = {};
    var useTable = {},
        useQuoteStyle = {};

    // Translate arguments
    constMappingTable[0] = 'HTML_SPECIALCHARS';
    constMappingTable[1] = 'HTML_ENTITIES';
    constMappingQuoteStyle[0] = 'ENT_NOQUOTES';
    constMappingQuoteStyle[2] = 'ENT_COMPAT';
    constMappingQuoteStyle[3] = 'ENT_QUOTES';

    /*
    // buggy?
    useTable = !isNaN(table) ? constMappingTable[table] : table ? table.toUpperCase() : 'HTML_SPECIALCHARS';
    useQuoteStyle = !isNaN(quote_style) ? constMappingQuoteStyle[quote_style] : quote_style ? quote_style.toUpperCase() :
        'ENT_COMPAT';
    */

    useTable      = table       ? table.toUpperCase()       : 'HTML_SPECIALCHARS';
    useQuoteStyle = quote_style ? quote_style.toUpperCase() : 'ENT_COMPAT';

    // debugging
    //log('useTable, useQuoteStyle:', useTable, useQuoteStyle);

    if (useTable !== 'HTML_SPECIALCHARS' && useTable !== 'HTML_ENTITIES') {
        throw new Error('Table: ' + useTable + ' not supported');
        // return false;
    }

    entities['38'] = '&amp;';
    if (useTable === 'HTML_ENTITIES') {
        entities['160'] = '&nbsp;';
        entities['161'] = '&iexcl;';
        entities['162'] = '&cent;';
        entities['163'] = '&pound;';
        entities['164'] = '&curren;';
        entities['165'] = '&yen;';
        entities['166'] = '&brvbar;';
        entities['167'] = '&sect;';
        entities['168'] = '&uml;';
        entities['169'] = '&copy;';
        entities['170'] = '&ordf;';
        entities['171'] = '&laquo;';
        entities['172'] = '&not;';
        entities['173'] = '&shy;';
        entities['174'] = '&reg;';
        entities['175'] = '&macr;';
        entities['176'] = '&deg;';
        entities['177'] = '&plusmn;';
        entities['178'] = '&sup2;';
        entities['179'] = '&sup3;';
        entities['180'] = '&acute;';
        entities['181'] = '&micro;';
        entities['182'] = '&para;';
        entities['183'] = '&middot;';
        entities['184'] = '&cedil;';
        entities['185'] = '&sup1;';
        entities['186'] = '&ordm;';
        entities['187'] = '&raquo;';
        entities['188'] = '&frac14;';
        entities['189'] = '&frac12;';
        entities['190'] = '&frac34;';
        entities['191'] = '&iquest;';
        entities['192'] = '&Agrave;';
        entities['193'] = '&Aacute;';
        entities['194'] = '&Acirc;';
        entities['195'] = '&Atilde;';
        entities['196'] = '&Auml;';
        entities['197'] = '&Aring;';
        entities['198'] = '&AElig;';
        entities['199'] = '&Ccedil;';
        entities['200'] = '&Egrave;';
        entities['201'] = '&Eacute;';
        entities['202'] = '&Ecirc;';
        entities['203'] = '&Euml;';
        entities['204'] = '&Igrave;';
        entities['205'] = '&Iacute;';
        entities['206'] = '&Icirc;';
        entities['207'] = '&Iuml;';
        entities['208'] = '&ETH;';
        entities['209'] = '&Ntilde;';
        entities['210'] = '&Ograve;';
        entities['211'] = '&Oacute;';
        entities['212'] = '&Ocirc;';
        entities['213'] = '&Otilde;';
        entities['214'] = '&Ouml;';
        entities['215'] = '&times;';
        entities['216'] = '&Oslash;';
        entities['217'] = '&Ugrave;';
        entities['218'] = '&Uacute;';
        entities['219'] = '&Ucirc;';
        entities['220'] = '&Uuml;';
        entities['221'] = '&Yacute;';
        entities['222'] = '&THORN;';
        entities['223'] = '&szlig;';
        entities['224'] = '&agrave;';
        entities['225'] = '&aacute;';
        entities['226'] = '&acirc;';
        entities['227'] = '&atilde;';
        entities['228'] = '&auml;';
        entities['229'] = '&aring;';
        entities['230'] = '&aelig;';
        entities['231'] = '&ccedil;';
        entities['232'] = '&egrave;';
        entities['233'] = '&eacute;';
        entities['234'] = '&ecirc;';
        entities['235'] = '&euml;';
        entities['236'] = '&igrave;';
        entities['237'] = '&iacute;';
        entities['238'] = '&icirc;';
        entities['239'] = '&iuml;';
        entities['240'] = '&eth;';
        entities['241'] = '&ntilde;';
        entities['242'] = '&ograve;';
        entities['243'] = '&oacute;';
        entities['244'] = '&ocirc;';
        entities['245'] = '&otilde;';
        entities['246'] = '&ouml;';
        entities['247'] = '&divide;';
        entities['248'] = '&oslash;';
        entities['249'] = '&ugrave;';
        entities['250'] = '&uacute;';
        entities['251'] = '&ucirc;';
        entities['252'] = '&uuml;';
        entities['253'] = '&yacute;';
        entities['254'] = '&thorn;';
        entities['255'] = '&yuml;';
    }

    if (useQuoteStyle !== 'ENT_NOQUOTES') {
        entities['34'] = '&quot;';
    }
    if (useQuoteStyle === 'ENT_QUOTES') {
        entities['39'] = '&#39;';
    }
    entities['60'] = '&lt;';
    entities['62'] = '&gt;';

    // ascii decimals to real symbols
    for (decimal in entities) {
        if (entities.hasOwnProperty(decimal)) {
            hash_map[String.fromCharCode(decimal)] = entities[decimal];
        }
    }

    return hash_map;
}

// http://www.joezimjs.com/javascript/using-marionette-to-display-modal-views/
// see also: http://lostechies.com/derickbailey/2012/04/17/managing-a-modal-dialog-with-backbone-and-marionette/
var ModalRegion = Marionette.Region.extend({
    constructor: function() {
        Marionette.Region.prototype.constructor.apply(this, arguments);

        this.ensureEl();
        this.$el.toggleClass('fade hide', true);
        this.$el.on('hidden', {region:this}, function(event) {
            event.data.region.close();
        });
    },

    onShow: function() {
        this.$el.modal('show');
    },

    onClose: function() {
        this.$el.modal('hide');
    }
});

// https://stackoverflow.com/questions/3898130/how-to-check-if-a-user-has-scrolled-to-the-bottom/10795797#10795797
var getDocumentHeight = function() {
    var D = document;
    return Math.max(
        D.body.scrollHeight, D.documentElement.scrollHeight,
        D.body.offsetHeight, D.documentElement.offsetHeight,
        D.body.clientHeight, D.documentElement.clientHeight
    );
}


// TODO: unify with sorting routine from ProjectModel
function sortCollectionByField(collection, fieldName, direction) {
    collection = collection.clone();
    var _this = collection;
    var _comparator_ascending = function(a, b) {
        a = a.get(_this.sort_key);
        b = b.get(_this.sort_key);
        return a > b ?  1
            : a < b ? -1
            :          0;
    };
    var _comparator_descending = function(a, b) { return _comparator_ascending(b, a); }
    collection.comparator = _comparator_ascending;
    if (_.str.startsWith(direction, 'd')) {
        collection.comparator = _comparator_descending;
    }
    collection.sort_key = fieldName;
    collection.sort();
    return collection;
}
