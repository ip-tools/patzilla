// -*- coding: utf-8 -*-
// (c) 2014-2018 Andreas Motl <andreas.motl@ip-tools.org>
require('blobjs');
var dataurl = require('dataurl').dataurl;
var saveAs = require('file-saver').saveAs;
var localforage = require('localforage');

require('backbone-relational');
require('localforage-backbone');


StoragePlugin = Marionette.Controller.extend({

    initialize: function(options) {
        console.log('StoragePlugin.initialize');
        this.database_version = '1.0.0';
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
                        type: 'patzilla.navigator.database',
                        description: 'IP Navigator database dump',
                        software_version: navigatorApp.config.get('setting.app.software.version'),
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

        log('StoragePlugin.dbexport');

        var _this = this;

        this.dump().then(function(backup) {
            _this.export_json_file('ip-navigator-database', backup);

        });

    },

    export_json_file: function(filename_prefix, data) {

        // Compute payload and filename.
        var payload = JSON.stringify(data, undefined, 4);
        var filename = filename_prefix + '_' + now_iso_filename() + '.json';

        // Write file.
        if (!payload) {
            navigatorApp.ui.notify('File export failed', {type: 'error', icon: 'icon-save'});
            return;
        }

        // Create Blob object and offer file for download.
        var blob = new Blob([payload], {type: "application/json"});
        saveAs(blob, filename);

        // Notify user.
        var size_kb = parseFloat((blob.size / 1000).toFixed(1))
        navigatorApp.ui.notify(
            'File "' + filename + '" exported successfully, size is ' + size_kb + ' kB.',
            {type: 'success', icon: 'icon-save'});

    },

    dbimport: function(kind, payload) {

        log('StoragePlugin.dbimport');
        var final_deferred = $.Deferred();

        var backup = payload;

        if (typeof(payload) == 'string') {

            if (_.string.startsWith(payload, 'data:')) {
                var payload_dataurl = dataurl.parse(payload);
                if (payload_dataurl) {
                    payload = payload_dataurl.data;
                }
                if (!payload_dataurl || !payload) {
                    var message = 'ERROR: Data URL format is invalid';
                    console.error(message + '; payload=' + payload);
                    navigatorApp.ui.notify(message, {type: 'error'});
                    final_deferred.reject(message);
                    return final_deferred;
                }
            }

            try {
                backup = JSON.parse(payload);

            } catch(error) {
                var msg = error.message;
                var message = 'ERROR: JSON format is invalid, ' + msg;
                console.error(message + '; payload=' + payload);
                navigatorApp.ui.notify(message, {type: 'error'});
                final_deferred.reject(message);
                return final_deferred;
            }
        }

        // Sanity checks
        //var filetype = backup && backup['metadata'] && backup['metadata']['type'];
        var filetype = dotresolve(backup, 'metadata.type');
        var database = dotresolve(backup, 'database');

        var filetype_should = 'patzilla.navigator.' + kind;

        if (filetype != filetype_should && filetype != 'elmyra.ipsuite.navigator.database') {
            var message = 'ERROR: Import format "' + filetype + '" is invalid for importing as "' + filetype_should + '".';
            console.error(message);
            navigatorApp.ui.notify(message, {type: 'error'});
            final_deferred.reject(message);
            return final_deferred;
        }

        if (!database) {
            var message = 'ERROR: Import file is empty.';
            console.error(message);
            navigatorApp.ui.notify(message, {type: 'error'});
            final_deferred.reject(message);
            return final_deferred;
        }

        var deferreds = [];
        _.each(_.keys(database), function(key) {
            var deferred = $.Deferred();
            deferreds.push(deferred.promise());
            var value = database[key];

            // Datamodel-specific restore behavior.
            // Merge project lists to get a union of (original, imported).
            // TODO: resolve project name collisions!
            if (key == 'Project' || key == 'Comment') {
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

            // Activate project
            navigatorApp.trigger('projects:initialize');

            navigatorApp.ui.notify(
                'File imported successfully',
                {type: 'success', icon: 'icon-folder-open-alt'});

            final_deferred.resolve();

        });

        return final_deferred;

    },

    dbreset: function(options) {

        log('dbreset');

        options = options || {};

        // make all data control widgets empty
        if (options.shutdown_gui) {
            navigatorApp.shutdown_gui();
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

    open_json_file: function(element) {

        var deferred = $.Deferred();

        // Read value of file element
        var file = element.files[0];
        if (!file) { return; }
        $(element).val(undefined);

        // Windows workaround
        var file_type = file.type;
        var running_in_hell = _.string.contains(navigator.userAgent, 'Windows');
        if (running_in_hell && file.type == '' && _.string.endsWith(file.name, '.json')) {
            file_type = 'application/json';
        }

        // Sanity checks
        if (file_type != 'application/json') {
            var message = 'ERROR: File type is ' + (file_type ? file_type : 'unknown') + ', but should be application/json';
            //log('import message:', message);
            navigatorApp.ui.notify(message, {type: 'error'});
            deferred.reject(message);
            return deferred.promise();
        }

        // Import file content to database
        var reader = new FileReader();
        reader.onload = function(e) {
            var payload = e.target.result;
            deferred.resolve(payload);
        };
        reader.onerror = function(e) {
            var message = 'ERROR: Could not read file ' + file.name + ', message=' + e.getMessage();
            //log('import message:', message);
            navigatorApp.ui.notify(message, {type: 'error'});
        }
        reader.readAsText(file);

        return deferred.promise();

    },

    confirm_load_data: function() {
        var deferred = $.Deferred();
        navigatorApp.ui.confirm(
            'You requested to load data from an import file which might render existing data inaccessible. ' +
            'The application will reload itself after the import task has finished. ' +
            '<br/><br/>' +
            'Please make sure you performed a backup using the "export" feature.' +
            '<br/><br/>' +
            'Continue import operation?').then(function() {
                deferred.resolve();
            });
        return deferred.promise();
    },

    setup_ui: function() {

        console.log('StoragePlugin.setup_ui');

        var _this = this;

        // Export database.
        $('#data-export-button').off('click');
        $('#data-export-button').on('click', function(e) {
            _this.dbexport($(this).parent());
        });

        // Import database from file.
        // https://developer.mozilla.org/en-US/docs/Using_files_from_web_applications
        $('#data-import-file').off('change');
        $('#data-import-file').on('change', function(e) {
            e.stopPropagation();
            e.preventDefault();

            var element = this;

            // Deactivate project / windows.onfocus.
            // Otherwise, the default project (e.g. "ad-hoc") would be recreated almost instantly.
            navigatorApp.project_deactivate();

            // Open file dialog.
            $.when(_this.open_json_file(element)).then(function(payload) {

                // Import database payload.
                $.when(_this.dbimport('database', payload)).then(function() {

                    // Reload environment.
                    $(element).trigger('import:ready');
                });
            });


        });

        $('#data-import-button').off('click');
        $('#data-import-button').on('click', function(e) {

            _this.confirm_load_data().then(function() {

                // Event handler for "import ready".
                $('#data-import-file').off('import:ready');
                $('#data-import-file').on('import:ready', function(e) {
                    setTimeout(function() {
                        window.location.reload();
                    }, 750);
                });

                // Start import by displaying file dialog.
                navigatorApp.project_deactivate();
                $('#data-import-file').trigger('click');

            });

        });


        // Drop database
        $('#database-wipe-button').off();
        $('#database-wipe-button').on('click', function(e) {

            navigatorApp.ui.confirm(
                'You requested to wipe the whole local database including custom keywords. ' +
                'All data will be lost.' +
                '<br/><br/>' +
                'Please make sure you performed a backup using the "export" feature. ' +
                '<br/><br/>' +
                'Are you sure to continue?').then(function() {

                // wipe the database
                _this.dbreset({shutdown_gui: true});

                // notify user about the completed action
                navigatorApp.ui.notify(
                    'Database wiped successfully. You should create a new project before starting over.',
                    {type: 'success', icon: 'icon-trash'});

            });

        });

    },

});


// Data storage components
navigatorApp.addInitializer(function(options) {

    var _this = this;

    // Set database name from "context" query parameter
    localforage.config({name: this.config.get('context')});

    // Set localforage driver
    // We use Local Storage here to make introspection easier.
    // TODO: Maybe disable on production
    localforage.setDriver(localforage.LOCALSTORAGE, function() {
        console.info("localforage: Driver is ready");
        _this.trigger('localforage:ready');
    });

    // Import database from url :-)
    // TODO: I'd like this to have storage.js make it on its own, but that'd be too late :-(
    //       check again what we could achieve...
    var database_dump = this.config.get('database');
    if (database_dump) {

        // When importing a database dump, we assign "context=viewer" a special meaning here:
        // the database scope will always be cleared beforehand to avoid project name collisions.
        // Ergo the "viewer" context is considered a *very transient* datastore.
        if (this.config.get('context') == 'viewer') {
            this.storage.dbreset();
        }

        // TODO: project and comment loading vs. application bootstrapping are not synchronized yet
        this.LOAD_IN_PROGRESS = true;

        // TODO: resolve project name collisions!
        this.storage.dbimport('database', database_dump);
    }

    this.register_component('storage');

});

navigatorApp.addInitializer(function(options) {

    this.storage = new StoragePlugin();

    this.listenTo(this, 'application:ready', function() {
        this.storage.setup_ui();
    });

    this.listenTo(this, 'results:ready', function() {
        this.storage.setup_ui();
    });

});
