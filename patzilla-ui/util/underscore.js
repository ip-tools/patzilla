// -*- coding: utf-8 -*-
// (c) 2013-2017 Andreas Motl, Elmyra UG
require('underscore');
require('underscore.string');


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
