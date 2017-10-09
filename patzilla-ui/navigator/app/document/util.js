// -*- coding: utf-8 -*-
// (c) 2013-2015 Andreas Motl, Elmyra UG

OpsBaseViewMixin = {

    bind_query_links: function(container) {

        var _this = this;

        // run search actions when clicking query-links
        container.find(".query-link").unbind('click');
        container.find(".query-link").on('click', function(event) {

            // add important parameters which reflect current gui state (e.g. selected project)
            var href = $(this).attr('href');
            var no_modifiers = $(this).data('no-modifiers');
            var params = opsChooserApp.permalink.query_parameters_viewstate(href, {'no_modifiers': no_modifiers});

            // TODO: Improve! Don't set "ops" here
            // regardless where the query originates from (e.g. datasource=review),
            // requests for query-links need switching to ops
            params['datasource'] = 'ops';

            // debugging
            //opsChooserApp.config.set('isviewer', true);

            // When in liveview, scrumble database query and viewstate parameters into opaque parameter token
            if (opsChooserApp.config.get('isviewer')) {

                event.preventDefault();
                event.stopPropagation();

                // Nail to liveview mode in any case
                params['mode'] = 'liveview';

                // Compute opaque link parameter and open url
                opsChooserApp.permalink.make_uri_opaque(params).then(function(url) {
                    open(url);
                });


                // Otherwise, serialize state into regular query parameters
            } else {
                $(this).attr('href', '?' + opsChooserApp.permalink.serialize_params(params));
            }

        });

    },


    bind_same_citations_links: function(container) {
        // bind user notification to all same citations links of "explore citation environment" fame
        //container.find('.same-citations-link').unbind('click');
        container.find('.same-citations-link').bind('click', function(event) {
            var citations_length = $(this).data('length');
            if (citations_length > 10) {
                event.preventDefault();
                event.stopPropagation();
                opsChooserApp.ui.notify(
                    'List is capped to the first 10 cited references. Sorry for this limitation.',
                    {type: 'warning', icon: 'icon-cut'});
                var _this = this;
                setTimeout(function() {
                    open($(_this).attr("href"));
                }, 3000);
            }
        });
    },

};
