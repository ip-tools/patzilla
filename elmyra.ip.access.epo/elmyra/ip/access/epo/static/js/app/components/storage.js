// -*- coding: utf-8 -*-
// (c) 2014 Andreas Motl, Elmyra UG

StoragePlugin = Marionette.Controller.extend({

    initialize: function(options) {

        console.log('StoragePlugin.initialize');
    },

    // register global hotkeys
    setup_ui: function() {

        // export database
        $('#data-export-button').unbind('click');
        $('#data-export-button').click(function(e) {

            var _this = this;

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
                $.when.apply($, deferreds).then(function() {

                    // prepare backup structure
                    var backup = {
                        database: database,
                        metadata: {
                            type: 'elmyra.ipsuite.navigator.backup',
                            description: 'Backupfile of Elmyra IP suite navigator',
                            software_version: software_version,
                            database_version: '1.0.0',
                            created: timestamp(),
                            useragent: navigator.userAgent,
                        },
                    };

                    // compute payload and filename
                    var payload = JSON.stringify(backup, undefined, 4);
                    var now = now_iso_human();
                    var filename = 'elmyra-navigator-backup ' + now + '.json';

                    // write file
                    var blob = new Blob([payload], {type: "application/json"});
                    saveAs(blob, filename);

                    // notify user
                    $(_this).parent().qnotify('Database exported successfully');

                });
            });
        });


        // import database
        // https://developer.mozilla.org/en-US/docs/Using_files_from_web_applications
        $('#data-import-file').unbind('change');
        $('#data-import-file').on('change', function(e) {
            e.stopPropagation();
            e.preventDefault();

            var file = this.files[0];
            $(this).val(undefined);

            var notifybox = $(this).parent();


            // sanity checks
            if (file.type != 'application/json') {
                $(notifybox).qnotify('ERROR: File type is ' + file.type + ', but should be application/json', {error: true});
                return;
            }


            var reader = new FileReader();
            reader.onload = function(e) {
                var payload = e.target.result;
                try {
                    var backup = jQuery.parseJSON(payload);

                } catch(error) {
                    var msg = error.message;
                    var message = 'ERROR: Could not parse JSON, ' + msg;
                    console.error(message);
                    $(notifybox).qnotify(message, {error: true});
                    return;
                }

                // more sanity checks
                //var filetype = backup && backup['metadata'] && backup['metadata']['type'];
                var filetype = dotresolve(backup, 'metadata.type');
                var database = dotresolve(backup, 'database');
                if (filetype != 'elmyra.ipsuite.navigator.backup' || !database) {
                    $(notifybox).qnotify('ERROR: Invalid backup format', {error: true});
                    return;
                }

                var deferreds = [];
                _.each(_.keys(database), function(key) {
                    var deferred = $.Deferred();
                    deferreds.push(deferred.promise());
                    var value = database[key];

                    // datamodel-specific restore behavior
                    // merge project lists to get a union of (original, imported)
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
                $.when.apply($, deferreds).then(function() {

                    Backbone.Relational.store.reset();

                    // compute any (first) valid project to be activated after import
                    try {
                        var project = backup['Project'] ? backup[backup['Project'][0]] : undefined;
                        var projectname = project.name;
                    } catch(error) {
                    }
                    if (!projectname) {
                        projectname = opsChooserApp.project.get('name');
                    }

                    // activate project
                    opsChooserApp.trigger('projects:initialize', projectname);

                    $(notifybox).qnotify('Database imported successfully');

                });
            };
            reader.onerror = function(e) {
                $(notifybox).qnotify('ERROR: Could not read file ' + file.name + ', message=' + e.getMessage(), {error: true});
            }
            reader.readAsText(file);

        });

        $('#data-import-button').unbind('dblclick');
        $('#data-import-button').dblclick(function(e) {
            $('#data-import-file').click();
        });


        // reset database
        $('#factory-reset-button').unbind('dblclick');
        $('#factory-reset-button').dblclick(function(e) {
            localforage.clear();
            Backbone.Relational.store = new Backbone.Store();
            if (opsChooserApp.projectChooserView) {
                opsChooserApp.projectChooserView.set_name();
            }
            $(this).parent().qnotify('Database wiped successfully', {error: true});
        });

    },

});

// setup plugin
opsChooserApp.addInitializer(function(options) {

    // handles the mechanics for all comment widgets on a whole result list
    var storage_plugin = new StoragePlugin();
    this.listenTo(this, 'application:ready', storage_plugin.setup_ui);

});
