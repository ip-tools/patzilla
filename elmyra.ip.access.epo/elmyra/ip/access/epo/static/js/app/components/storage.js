// -*- coding: utf-8 -*-
// (c) 2014 Andreas Motl, Elmyra UG

StoragePlugin = Marionette.Controller.extend({

    initialize: function(options) {
        console.log('StoragePlugin.initialize');
        this.database_version = '0.0.1';
    },

    dump: function() {

        var _this = this;
        var deferred = $.Deferred();

        localforage.keys().then(function(keys) {
            var database = {};
            var deferreds = [];

            // gather all entries
            _.each(keys, function(key) {
                var deferred = $.Deferred();
                deferreds.push(deferred);
                localforage.getItem(key).then(function(value) {
                    database[key] = value;
                    deferred.resolve();
                });
            });

            // save to file
            $.when(deferreds_bundle(deferreds)).then(function() {

                // prepare database dump structure
                var backup = {
                    database: database,
                    metadata: {
                        type: 'elmyra.ipsuite.navigator.database',
                        description: 'Database dump of Elmyra IP suite navigator',
                        software_version: opsChooserApp.config.get('setting.app.software.version'),
                        database_version: _this.database_version,
                        database_name: localforage.config('name'),
                        created: timestamp(),
                        useragent: navigator.userAgent,
                    },
                };

                deferred.resolve(backup);

            });
        });

        return deferred.promise();

    },

    dbexport: function() {

        var _this = this;

        this.dump().then(function(backup) {

            // compute payload and filename
            var payload = JSON.stringify(backup, undefined, 4);
            var now = now_iso_human();
            var filename = 'elmyra-ipsuite-navigator.' + now + '.database.json';

            // write file
            if (!payload) {
                opsChooserApp.ui.notify('Database export failed', {type: 'error', icon: 'icon-save'});
                return;
            }
            var blob = new Blob([payload], {type: "application/json"});
            saveAs(blob, filename);

            // notify user
            opsChooserApp.ui.notify('Database exported successfully', {type: 'success', icon: 'icon-save'});

        });

    },

    dbimport: function(payload) {

        log('StoragePlugin.dbimport');

        var backup = payload;

        if (typeof(payload) == 'string') {

            if (_.string.startsWith(payload, 'data:')) {
                var payload_dataurl = dataurl.parse(payload);
                if (payload_dataurl) {
                    payload = payload_dataurl.data;
                }
                if (!payload_dataurl || !payload) {
                    var message = 'ERROR: data URL format is invalid';
                    console.error(message + '; payload=' + payload);
                    opsChooserApp.ui.notify(message, {type: 'error'});
                    return;
                }
            }

            try {
                backup = jQuery.parseJSON(payload);

            } catch(error) {
                var msg = error.message;
                var message = 'ERROR: JSON format is invalid, ' + msg;
                console.error(message + '; payload=' + payload);
                opsChooserApp.ui.notify(message, {type: 'error'});
                return;
            }
        }

        // more sanity checks
        //var filetype = backup && backup['metadata'] && backup['metadata']['type'];
        var filetype = dotresolve(backup, 'metadata.type');
        var database = dotresolve(backup, 'database');
        if (filetype != 'elmyra.ipsuite.navigator.database' || !database) {
            var message = 'ERROR: Database dump format is invalid';
            console.error(message);
            opsChooserApp.ui.notify(message, {type: 'error'});
            return;
        }

        var deferreds = [];
        _.each(_.keys(database), function(key) {
            var deferred = $.Deferred();
            deferreds.push(deferred.promise());
            var value = database[key];

            // datamodel-specific restore behavior
            // merge project lists to get a union of (original, imported)
            // TODO: resolve project name collisions!
            if (key == 'Project') {
                localforage.getItem(key).then(function(original) {
                    if (original && value) {
                        value = _.union(original, value);
                    }
                    localforage.setItem(key, value).then(function() {
                        deferred.resolve();
                    });
                });

            } else {
                localforage.setItem(key, value).then(function(value) {
                    deferred.resolve();
                });
            }
        });

        $.when(deferreds_bundle(deferreds)).then(function() {

            // TODO: get rid of this! here!
            // This should trigger a complete application model bootstrap (coll1.fetch(), coll2.fetch(), etc.),
            // which should most probably be implemented at a central place.

            Backbone.Relational.store.reset();

            // activate project
            opsChooserApp.trigger('projects:initialize');

            opsChooserApp.ui.notify('Database imported successfully', {type: 'success'});

        });

    },

    dbreset: function(options) {

        options = options || {};

        // make all data control widgets empty
        if (options.shutdown_gui) {
            opsChooserApp.shutdown_gui();
        }

        // reset state of orm
        Backbone.Relational.store.reset();
        //Backbone.Relational.store = new Backbone.Store();

        // wipe the data store
        localforage.clear();
    },

    setup_ui: function() {

        console.log('StoragePlugin.setup_ui');

        var _this = this;

        // export database
        $('#data-export-button').unbind('click');
        $('#data-export-button').on('click', function(e) {
            _this.dbexport($(this).parent());
        });

        // import database
        // https://developer.mozilla.org/en-US/docs/Using_files_from_web_applications
        $('#data-import-file').unbind('change');
        $('#data-import-file').on('change', function(e) {
            e.stopPropagation();
            e.preventDefault();

            var file = this.files[0];
            $(this).val(undefined);

            // sanity checks
            if (file.type != 'application/json') {
                var message = 'ERROR: File type is ' + file.type + ', but should be application/json';
                //log('import message:', message);
                opsChooserApp.ui.notify(message, {type: 'error'});
                return;
            }


            var reader = new FileReader();
            reader.onload = function(e) {
                var payload = e.target.result;
                _this.dbimport(payload);

            };
            reader.onerror = function(e) {
                var message = 'ERROR: Could not read file ' + file.name + ', message=' + e.getMessage();
                //log('import message:', message);
                opsChooserApp.ui.notify(message, {type: 'error'});
            }
            reader.readAsText(file);

        });

        $('#data-import-button').unbind('click');
        $('#data-import-button').on('click', function(e) {
            $('#data-import-file').click();
        });


        // reset database
        $('#factory-reset-button').unbind();
        $('#factory-reset-button').click(function(e) {

            bootbox.confirm('<h4><span class="alert alert-danger">This will wipe the whole local database. Are you sure?</span></h4>', function(wipe_ack) {
                if (wipe_ack) {

                    // wipe the database
                    _this.dbreset({shutdown_gui: true});

                    // send some notifications
                    opsChooserApp.ui.notify('Database wiped successfully. You should create a new project before starting over.', {type: 'success'});
                }
            });

        });

    },

});

// setup plugin (DONE in app/main.js, because we need it early!)
/*
opsChooserApp.addInitializer(function(options) {
});
*/
