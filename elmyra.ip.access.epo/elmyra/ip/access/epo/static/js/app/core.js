// -*- coding: utf-8 -*-
// (c) 2013,2014 Andreas Motl, Elmyra UG

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

            var tpl = _.template($('#cornice-error-template').html());
            var alert_html = tpl(error);
            $('#alert-area').append(alert_html);
        });
    }
}

function boot_application() {

    console.log('boot_application');

    // initialize content which still resides on page level (i.e. no template yet)
    $('#query').val(opsChooserApp.config.get('query'));
    $('#ui-title').html(getconfig('setting.ui.page.title'));
    $('#ui-subtitle').html(getconfig('setting.ui.page.subtitle'));
    $('#ui-statusline').html(getconfig('setting.ui.page.statusline'));
    $('#ui-productname').html(getconfig('setting.ui.productname'));
    $('#ui-footer').html(getconfig('setting.ui.page.footer', {after: '<br/>'}));
    $('#ui-footer-version').html(getconfig('setting.ui.version', {after: '<br/>'}));

    // propagate "datasource" query parameter
    var datasource = opsChooserApp.config.get('datasource');
    if (datasource) {
        opsChooserApp.set_datasource(datasource);
    }

    // hide pagination- and metadata-area to start from scratch
    opsChooserApp.ui.reset_content();

    // propagate opaque error messages to alert area
    propagate_opaque_errors();

    opsChooserApp.trigger('application:ready');

    opsChooserApp.ui.do_element_visibility();

}
