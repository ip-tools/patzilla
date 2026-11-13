// -*- coding: utf-8 -*-
// (c) 2014,2017 Andreas Motl, Elmyra UG
'use strict';

// Two help pages, wired with @mnjs/router.
// https://marionettejs.com/docs/packages/router/
// https://marionettejs.com/docs/guides/routing/

require('patzilla.lib.backbone');
require('patzilla.lib.marionette');
require('patzilla.lib.bootstrap');
require('patzilla.navigator.style');

import { Router, RouteApplication, historyDriver } from '@mnjs/router';
import { HotkeysHelpView } from 'patzilla.navigator.components.hotkeys/hotkeys-help';
import { IFIClaimsHandbookView } from 'patzilla.access.ificlaims-help';

const HelpApplication = RouteApplication.extend({
  region: { el: '#content-region' },

  // FIXME: Must not hard-code `/navigator` prefix. How?
  routes: {
    '/navigator/help/hotkeys': { name: 'hotkeys', handler: 'hotkeys' },
    '/navigator/help/ificlaims': { name: 'ificlaims', handler: 'ificlaims' },
  },

  hotkeys() {
    $('#title-container').text('Hotkeys overview');
    this.showView(new HotkeysHelpView());
  },

  ificlaims() {
    $('#title-container').text('Benutzerhandbuch für die Suche bei IFI Claims');
    this.showView(new IFIClaimsHandbookView());
  },
});

const router = new Router({ driver: historyDriver() });
const help = new HelpApplication();
help.mountRoutes(router);

$(function() {
  help.start();
  router.start();
});
