// -*- coding: utf-8 -*-
// (c) 2014 Andreas Motl, Elmyra UG

NavigatorHelp = Backbone.Marionette.Application.extend({
});

navigatorHelp = new NavigatorHelp({});

navigatorHelp.addRegions({
    region_hotkeys: "#help-hotkeys-region",
});

navigatorHelp.addInitializer(function(options) {
});

$(document).ready(function() {
    console.log("document.ready");
    navigatorHelp.start();
});
