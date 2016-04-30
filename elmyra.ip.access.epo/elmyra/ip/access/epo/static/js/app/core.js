// -*- coding: utf-8 -*-
// (c) 2013-2016 Andreas Motl, Elmyra UG

function getconfig(name, options) {
    options = options || {};
    var label = opsChooserApp.config.get(name);
    if (label) {
        if (options.before) {
            label = options.before + label;
        }
        if (options.after) {
            label = label + options.after;
        }
    }
    return label;
}

function propagate_opaque_errors() {
    var status = opsChooserApp.config.get('opaque.meta.status');
    if (status == 'error') {
        var errors = opsChooserApp.config.get('opaque.meta.errors');
        _.each(errors, function(error) {

            if (error.location == 'JSON Web Token' && error.description == 'expired') {
                error.description =
                    'We are sorry, it looks like the validity time of this link has expired at ' + error.jwt_expiry_iso + '.' +
                        '<br/><br/>' +
                        'Please contact us at <a href="mailto:support@elmyra.de">support@elmyra.de</a> for any commercial plans.';
            }
            if (error.location == 'JSON Web Signature') {
                error.description = 'It looks like the token used to encode this request is invalid.' + ' (' + error.description + ')'
            }

            // TODO: Streamline error forwarding
            var response = {
                'status': 'error',
                'errors': [error]
            }
            opsChooserApp.ui.propagate_cornice_errors(response);

        });
    }
}
