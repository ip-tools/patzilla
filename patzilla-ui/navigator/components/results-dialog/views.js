// -*- coding: utf-8 -*-
// (c) 2014-2015 Andreas Motl, Elmyra UG
require('patzilla.lib.marionette-modalregion');

GenericResultView = Backbone.Marionette.ItemView.extend({

    tagName: "div",
    id: "result-view",
    className: "modal",
    template: require('./widget.html'),

    indicate_activity: function(active) {
        if (active) {
            this.$el.find('#result-busy').show();
            this.$el.find('#result-ready').hide();

        } else {
            this.$el.find('#result-busy').hide();
            this.$el.find('#result-ready').show();
        }
    },

    user_message: function(message, kind) {
        $('#result-info').empty();
        return navigatorApp.ui.user_alert(message, kind, '#result-info');
    },

    templateHelpers: {
    },

    events: {
    },

    setup_numberlist_buttons: function(numberlist) {

        var _this = this;
        var numberlist_string = numberlist.join('\n');

        // setup copy-to-clipboard button
        var clipboard_button = this.$el.find('#result-to-clipboard-button');
        navigatorApp.ui.copy_to_clipboard_bind_button('text/plain', numberlist_string, {element: clipboard_button[0], wrapper: this.el});

        // setup insert-to-basket button
        var basket_button = this.$el.find('#result-to-basket-button');
        basket_button.off('click');
        basket_button.on('click', function(event) {
            $('#result-to-basket-indicator').removeClass('icon-plus').addClass('icon-spinner icon-spin');
            setTimeout(function() {
                $.when(navigatorApp.basketModel.add_multi(numberlist, {reset_seen: true})).then(function() {
                    $('#result-to-basket-indicator').removeClass('icon-spinner icon-spin').addClass('icon-plus');
                    var message = 'Added ' + numberlist.length + ' patent numbers to document collection.';
                    navigatorApp.ui.notify(message, {type: 'success', icon: 'icon-plus', wrapper: _this.el});
                });
            }, 50);
        });

    },

    hide_buttons: function() {
        this.$el.find('#result-to-clipboard-button').hide();
        this.$el.find('#result-to-basket-button').hide();
    },

    hide_button_to_basket: function() {
        this.$el.find('#result-to-basket-button').hide();
    },

    onShow: function() {
        this.start();
    },

    start: function() {

        var _this = this;

        this.indicate_activity(true);
        this.user_message(
            'Fetching results from data source "' + _this.model.get('datasource') + '", ' +
                'please stand by. &nbsp; <i class="spinner icon-refresh icon-spin"></i>', 'info');

        var fetcher = this.fetcher_factory();
        if (!fetcher) return;

        fetcher.start().then(function(response) {

            // transfer data
            _this.setup_data(response);

            // notify user
            _this.indicate_activity(false);
            var length = NaN;
            if (_.isArray(response)) {
                length = response.length;
            }
            if (_.isObject(response)) {
                length = Object.keys(response).length;
            }
            var message =
                (isNaN(length) ? 'No' : length) +
                    ' result item(s) fetched successfully from data source "' + _this.model.get('datasource') + '".';
            if (_this.message_more) {
                message += _this.message_more;
            }
            _this.user_message(message, 'success');

        }).fail(function(response, error) {

                console.warn('error:  ', error);

                // notify user
                _this.indicate_activity(false);

                var message = response;
                try {

                    // Try to decode main response from JSON
                    var data = JSON.parse(response);
                    var responseText = '';
                    if (data['responseText']) {
                        responseText = data['responseText'];
                        data['responseText'] = '...';
                    }

                    // Try to decode responseText from JSON
                    try {
                        var responseTextData = JSON.parse(responseText);
                        responseText = '<pre>' + JSON.stringify(responseTextData, null, 2) + '</pre>';
                    } catch (ex) {
                        console.warn('Data source crawler could not parse "responseText":', ex);
                    }

                    // Build user-facing error message
                    message =
                        '<pre>' + JSON.stringify(data, null, 2) + '</pre>' +
                            (responseText ? '<br/>' + responseText : '');

                } catch (ex) {
                    console.warn('Data source crawler could not parse main error response:', ex);
                }

                var user_message =
                    'Error while fetching results from data source "' + _this.model.get('datasource') + '". ' +
                        'Reason: ' + message;
                console.warn('message:', user_message);
                _this.user_message(user_message, 'error');

            });

    },

});

function make_modal_view(view_class, model, options) {
    options = options || {};
    var modal = new ModalRegion({el: '#modal-area'});

    var view_options = {model: model};
    $.extend(view_options, options);
    var view = new view_class(view_options);
    modal.show(view);
}
