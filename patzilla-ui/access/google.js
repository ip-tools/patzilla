// -*- coding: utf-8 -*-
// (c) 2014 Andreas Motl <andreas.motl@ip-tools.org>
require('./base.js');

GooglePatentSearch = DatasourceSearch.extend({
    url: '/api/google/published-data/search',

    search: function(search_info, query, options) {
        this.perform(query, options).done(function(response) {
            options = options || {};

            navigatorApp.trigger('search:success', search_info);

            navigatorApp.propagate_datasource_message(response);

            // propagate keywords
            log('this.keywords:', this.keywords);
            navigatorApp.metadata.set('keywords', this.keywords);

            // debugging
            console.log('google response:', response);
            console.log('google keywords:', this.keywords);

            var publication_numbers = response['numbers'];
            var hits = response['hits'];

            if (publication_numbers) {

                // TODO: return pagesize from backend
                options.remote_limit = 100;

                navigatorApp.perform_listsearch(options, query, publication_numbers, hits, 'pn', 'OR').done(function() {

                    // propagate upstream message again, because "perform_listsearch" clears it; TODO: enhance mechanics!
                    navigatorApp.propagate_datasource_message(response);

                    if (hits == null) {
                        navigatorApp.ui.user_alert(
                            'Result count unknown. At Google Patents, sometimes result counts are not displayed. ' +
                            "Let's assume 1000 to make the paging work.", 'warning');
                    }

                    if (hits > navigatorApp.metadata.get('maximum_results')['google']) {
                        navigatorApp.ui.user_alert(
                            'Total results ' + hits + '. From Google Patents, the first 1000 results are accessible. ' +
                            'You might want to narrow your search by adding more search criteria.', 'warning');
                    }
                });
            }

        });
    },

});
