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
