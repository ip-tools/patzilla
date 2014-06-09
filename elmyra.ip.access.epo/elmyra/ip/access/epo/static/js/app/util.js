// -*- coding: utf-8 -*-
// (c) 2013,2014 Andreas Motl, Elmyra UG

function to_list(value) {
    return _.isArray(value) && value || [value];
}

function now_iso() {
    return moment().format();
}

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
