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
            var filename = 'ipsuite-database_' + now_iso_filename() + '.json';

            // write file
            if (!payload) {
                _ui.notify('Database export failed', {type: 'error', icon: 'icon-save'});
                return;
            }
            var blob = new Blob([payload], {type: "application/json"});
            saveAs(blob, filename);

            // notify user
            var size_kb = Math.round(blob.size / 1000);
            _ui.notify(
                'Database exported successfully, size is ' + size_kb + 'kB.',
                {type: 'success', icon: 'icon-save'});

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
                    _ui.notify(message, {type: 'error'});
                    return;
                }
            }

            try {
                backup = jQuery.parseJSON(payload);

            } catch(error) {
                var msg = error.message;
                var message = 'ERROR: JSON format is invalid, ' + msg;
                console.error(message + '; payload=' + payload);
                _ui.notify(message, {type: 'error'});
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
            _ui.notify(message, {type: 'error'});
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

            _ui.notify(
                'Database imported successfully',
                {type: 'success', icon: 'icon-folder-open-alt'});

        });

    },

    dbreset: function(options) {

        log('dbreset');

        options = options || {};

        // make all data control widgets empty
        if (options.shutdown_gui) {
            opsChooserApp.shutdown_gui();
        }

        // reset state of orm
        Backbone.Relational.store.reset();
        //Backbone.Relational.store = new Backbone.Store();

        // wipe the data store
        localforage.clear().then(function() {
            log('localforage.clear SUCCESS');
        }, function() {
            log('localforage.clear FAIL');
        });

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

            // deactivate project / windows.onfocus
            // otherwise, the default project (e.g. "ad-hoc") would be recreated almost instantly
            opsChooserApp.project_deactivate();

            var file = this.files[0];
            if (!file) { return; }
            $(this).val(undefined);

            // Windows workaround
            var file_type = file.type;
            var running_in_hell = _.string.contains(navigator.userAgent, 'Windows');
            if (running_in_hell && file.type == '' && _.string.endsWith(file.name, '.json')) {
                file_type = 'application/json';
            }

            // sanity checks
            if (file_type != 'application/json') {
                var message = 'ERROR: File type is ' + (file_type ? file_type : 'unknown') + ', but should be application/json';
                //log('import message:', message);
                _ui.notify(message, {type: 'error'});
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
                _ui.notify(message, {type: 'error'});
            }
            reader.readAsText(file);

        });

        $('#data-import-button').unbind('click');
        $('#data-import-button').on('click', function(e) {
            opsChooserApp.project_deactivate();
            $('#data-import-file').click();
        });


        // reset database
        $('#database-wipe-button').unbind();
        $('#database-wipe-button').click(function(e) {

            _ui.confirm('This will wipe the whole local database including custom keywords. Are you sure?').then(function() {

                // wipe the database
                _this.dbreset({shutdown_gui: true});

                // notify user about the completed action
                _ui.notify(
                    'Database wiped successfully. You should create a new project before starting over.',
                    {type: 'success', icon: 'icon-trash'});

            });

        });

    },

});

// setup plugin (DONE in app/main.js, because we need it early!)
/*
opsChooserApp.addInitializer(function(options) {
});
*/
