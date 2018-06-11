// -*- coding: utf-8 -*-
// (c) 2014-2018 Andreas Motl <andreas.motl@ip-tools.org>
require('./models');
require('./views');

// Register data source adapter with application
navigatorApp.addInitializer(function(options) {
    this.register_datasource('sip', {

        // The title used when referencing this data source to the user
        title: 'SIP',

        // The data source adapter classes
        adapter: {
            search: SipSearch,
            entry: SipResultEntry,
            crawl: SipCrawler,
            result_item_view: SipResultView,
        },

        // Settings for query builder
        querybuilder: {

            // Hotkey for switching to this data source
            hotkey: 'ctrl+shift+s',

            // Which additional extra fields can be queried for
            extra_fields: ['pubdate'],

            // Whether to disable the raw query textarea
            disable_raw_query: true,

            // Whether to disable the field chooser
            disable_field_chooser: true,

            // Does this data source have fulltext modifiers?
            enable_fulltext_modifiers: true,

            // Enable the "remove/replace family members" feature
            enable_remove_family_members: true,

            // Enable the "expand family members" feature
            enable_expand_family_members: true,

            // When clicking a mode button which augments search behavior, recompute upstream query expression
            // for search backends where query_data modifiers already influence the expression building.
            // With "SIP", we inject the attribute 'fullfamily="true"' into the XML nodes.
            recompute_query_on_modechange: true,

            // Which placeholders to use for comfort form demo criteria
            placeholder: {
                patentnumber: 'single',
            },

            // Bootstrap color variant used for referencing this data source in a query history entry
            history_label_color: 'warning',

        },

        // Whether this data source provides a result view
        has_resultview: true,

    });
});
