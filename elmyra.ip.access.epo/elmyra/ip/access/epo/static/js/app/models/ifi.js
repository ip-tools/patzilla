// -*- coding: utf-8 -*-
// (c) 2015-2017 Andreas Motl, Elmyra UG

IFIClaimsSearch = DatasourceSearch.extend({
    url: '/api/ifi/published-data/search',
});

IFIClaimsResultEntry = Backbone.Model.extend({

    defaults: {
    },

});

IFIClaimsCrawler = DatasourceCrawler.extend({

    initialize: function(options) {
        log('IFIClaimsCrawler.initialize');
        options = options || {};
        options.datasource = 'ifi';
        this.__proto__.constructor.__super__.initialize.apply(this, arguments);
    },

});

IFIClaimsFulltext = Marionette.Controller.extend({

    initialize: function(document_number) {
        log('IFIClaimsFulltext.initialize');
        this.document_number = document_number;

        this.description_fragments = [
            {key: 'technical-field', original_label: 'The technical field of', label: 'Technical field'},
            {key: 'background-art', original_label: 'Background technology', label: 'Background technology'},
            {key: 'summary-of-invention.tech-problem', label: 'Summary of invention » Technological problem' },
            {key: 'summary-of-invention.tech-solution', label: 'Summary of invention » Technological solution' },
            {key: 'description-of-embodiments', label: 'Description of embodiments' },
            {key: 'disclosure', original_label: 'The content of invention', label: 'Content of invention' },
            {key: 'description-of-drawings', original_label: 'Specification attached drawing', label: 'Description of drawings' },
            {key: 'mode-for-invention', label: 'Specific implementing manner' },
        ];

    },

    get_claims: function() {

        var _this = this;
        var deferred = $.Deferred();

        var url = _.template('/api/ifi/download/<%= document_number %>.json')({ document_number: this.document_number});
        $.ajax({url: url, async: true})
            .success(function(response) {
                if (response) {
                    log('response:', response);

                    var document = response['patent-document'];

                    if (!document.claims) {
                        deferred.reject({html: 'No data available'});
                        return deferred.promise();
                    }

                    // Serialize claims to HTML
                    var claims_parts = [];

                    // Variant A: Multilanguage Array, e.g. FR2853955A1, JPH11195384A
                    if (_.isArray(document.claims)) {
                        _.each(document.claims, function(claim_container) {
                            var lang = claim_container['@lang'];
                            if (lang == 'EN') {
                                claims_parts = _this.parse_claim_list(to_list(claim_container.claim));
                                return;
                            }
                        });

                    // Variant B: Array, e.g. CN104154791B
                    } else if (_.isArray(document.claims.claim)) {
                        claims_parts = _this.parse_claim_list(document.claims.claim);

                    // Variant C: Object, e.g. WO2017016928A1
                    } else if (_.isObject(document.claims.claim)) {
                        claims_parts = _this.parse_claim_list(document.claims.claim['claim-text']);

                    }

                    var data = {
                        html: claims_parts.join('<br/><br/>'),
                        lang: document.claims['@lang'],
                    };
                    deferred.resolve(data);
                }
            }).error(function(error) {
                console.warn('Error while fetching claims from IFI Claims for', _this.document_number, error);
                deferred.reject({html: 'Error fetching data'});
            });

        return deferred.promise();

    },

    parse_claim_list: function(claim_list) {
        var _this = this;
        var claims_parts = [];
        _.each(claim_list, function(claim) {
            var text = _this.parse_claim_text(claim);
            claims_parts.push(text);
        });
        return claims_parts;
    },

    parse_claim_text: function(container) {
        var number;
        var text;
        if (_.isArray(container['claim-text'])) {
            // e.g. RU2015121704A
            return this.parse_claim_list(container['claim-text']).join('<br/>');
        } else if (_.isObject(container['claim-text'])) {
            // e.g. CN104154791B
            number = _.string.ltrim(container['@num'], '0');
            text = _.string.ltrim(container['claim-text']['$t']);
        } else {
            // e.g. WO2017016928A1
            text = container['$t'];
        }

        var result;
        if (number) {
            if (_.string.startsWith(text, number + ' ')) {
                text = text.replace(number + ' ', '');
            }
            if (_.string.startsWith(text, number + '. ')) {
                text = text.replace(number + '. ', '');
            }
            result = number + '. ' + text;
        } else {
            result = text;
        }

        // JPH11195384A
        if (_.string.contains(text, '< Claim 1 >')) {
            result = text.replace(/(< Claim \d+ >)/g, '<br/><br/>$1<br/>');
        }

        return result;
    },

    get_description: function() {

        var _this = this;
        var deferred = $.Deferred();

        var url = _.template('/api/ifi/download/<%= document_number %>.json')({ document_number: this.document_number});
        $.ajax({url: url, async: true})
            .success(function(response) {
                if (response) {
                    //log('response:', response);

                    var document = response['patent-document'];

                    if (!document.description) {
                        deferred.reject({html: 'No data available'});
                        return deferred.promise();
                    }

                    // Serialize description to HTML
                    var description_parts = [];

                    // Variant A: Multilanguage Array, KR20150133732A
                    if (_.isArray(document.description)) {
                        _.each(document.description, function(description_container) {
                            var lang = description_container['@lang'];
                            if (lang == 'EN') {
                                description_parts = _this.parse_description_container(description_container);
                                return;
                            }
                        });

                    // Variant B: With sections, e.g. CN104154791A
                    } else if (!document.description.p) {
                        description_parts = _this.parse_description_container(document.description);

                    // Variant C: Without sections, e.g. CN105674358A
                    } else if (_.isArray(document.description.p)) {
                        description_parts = _this.parse_description_list(document.description.p);
                        description_parts = _.map(description_parts, function(text) {
                            if (_.string.startsWith(text, '【 ')) {
                                text = _.string.capitalize(text.replace('【 ', '').replace(' 】', ''));
                                _.each(_this.description_fragments, function(fragment_spec) {
                                    if (fragment_spec.original_label == text) {
                                        text = _this.parse_description_text({'$t': text}, fragment_spec, 0);
                                    }
                                });
                            }
                            return text;
                        });

                    }
                    //log('description_parts:', description_parts);

                    var data = {
                        html: description_parts.join('<br/><br/>'),
                        lang: document.description['@lang'],
                    };
                    deferred.resolve(data);
                }

            }).error(function(error) {
                console.warn('Error while fetching description from IFI Claims for', _this.document_number, error);
                deferred.reject({html: 'Error fetching data'});
            });

        return deferred.promise();

    },

    parse_description_container: function(description_container) {

        var _this = this;

        // Order of fragments

        var description_parts = [];
        if (description_container.p) {
            description_parts = this.parse_description_list(description_container.p);

        } else {
            _.each(this.description_fragments, function(fragment_spec) {
                var fragment_name = fragment_spec['key'];
                try {
                    var value = dotted_reference(description_container, fragment_name);
                    //log(fragment_name, value);
                    if (!value) {
                        return;
                    }
                    description_parts = description_parts.concat(_this.parse_description_list(value.p, fragment_spec));
                } catch(ex) {
                    // pass
                }
            });
        }
        return description_parts;
    },

    parse_description_list: function(description_list, fragment_spec) {
        var _this = this;
        var description_parts = [];

        var index = 0;
        _.each(to_list(description_list), function(part) {
            var text = _this.parse_description_text(part, fragment_spec, index);
            description_parts.push(text);
            index++;
        });

        /*
        _.each(description_list, function(part) {
            var text = part['$t'];

            // When entry carries caption, perform
            if (_.string.startsWith(text, '【 ')) {
                text = _.string.capitalize(text.replace('【 ', '').replace(' 】', ''));
                //text = _this.patch_description_text(text);
            }
            description_parts.push(text);
        });
        */

        return description_parts;
    },

    parse_description_text: function(part, fragment_spec, index) {

        var heading = '';
        var text = part['$t'];

        // When first index carries caption, perform rewording and emphasis
        if (fragment_spec && index == 0) {

            // When text carries caption, perform
            if (fragment_spec.original_label == text) {

                // a) rewording
                text = text.replace(fragment_spec.original_label, fragment_spec.label);
            }

            if (fragment_spec.label == text) {
                // b) emphasize
                heading = '<b>' + text + '</b>';
                text = '';
            } else {
                heading = '<b>' + fragment_spec.label + '</b>' + '<br/><br/>';
            }

        }

        if (part['@num']) {
            text = '[' + part['@num'] + '] ' + text;
        }

        // JPH11195384A
        if (_.string.contains(text, '< 0001 >')) {
            text = text.replace(/(< \d+ >)/g, '<br/><br/>$1<br/>');
        }

        return heading + text;
    },

    get_abstract: function(language) {

        var _this = this;
        var deferred = $.Deferred();

        var url_tpl = '/api/depatisconnect/<%= document_number %>/abstract'
        if (language) {
            url_tpl += '?language=<%= language %>'
        }
        var url = _.template(url_tpl)({ document_number: this.document_number, language: language});
        $.ajax({url: url, async: true})
            .success(function(payload) {
                if (payload && payload['xml']) {
                    var response = {
                        html: payload['xml'],
                        lang: payload['lang'],
                    };
                    deferred.resolve(response);

                } else {
                    console.warn('DEPATISconnect: Empty abstract for', _this.document_number);
                    deferred.reject({html: 'Abstract for this document is empty, see original data source'});
                }
            }).error(function(error) {
                console.warn('DEPATISconnect: Error while fetching abstract for', _this.document_number, error);
                deferred.reject({html: 'No data available', error: error});
            });

        return deferred.promise();

    },

});
