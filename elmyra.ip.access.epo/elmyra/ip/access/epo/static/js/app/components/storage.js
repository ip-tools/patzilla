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
            $.when.apply($, deferreds).then(function() {

                // prepare database dump structure
                var backup = {
                    database: database,
                    metadata: {
                        type: 'elmyra.ipsuite.navigator.database',
                        description: 'Database dump of Elmyra IP suite navigator',
                        software_version: software_version,
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

    dbexport: function(notifybox) {

        var _this = this;

        this.dump().then(function(backup) {

            // compute payload and filename
            var payload = JSON.stringify(backup, undefined, 4);
            var now = now_iso_human();
            var filename = 'elmyra-ipsuite-navigator.' + now + '.database.json';

            // write file
            if (!payload) {
                $(notifybox).qnotify('Database export failed', {error: true});
                return;
            }
            var blob = new Blob([payload], {type: "application/json"});
            saveAs(blob, filename);

            // notify user
            $(notifybox).qnotify('Database exported successfully');

        });

    },

    dbimport: function(payload, notifybox) {

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
                    $(notifybox).qnotify(message, {error: true});
                    return;
                }
            }

            try {
                backup = jQuery.parseJSON(payload);

            } catch(error) {
                var msg = error.message;
                var message = 'ERROR: JSON format is invalid, ' + msg;
                console.error(message + '; payload=' + payload);
                $(notifybox).qnotify(message, {error: true});
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
            $(notifybox).qnotify(message, {error: true});
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

            // TODO: get rid of this! here!
            // This should trigger a complete application model bootstrap (coll1.fetch(), coll2.fetch(), etc.),
            // which should most probably be implemented at a central place.

            Backbone.Relational.store.reset();

            // compute any (first) valid project to be activated after import
            try {
                var project = backup['Project'] ? backup[backup['Project'][0]] : undefined;
                var projectname = project.name;
            } catch(error) {
            }

            // use last selected project name
            if (!projectname) {
                if (opsChooserApp.project) {
                    projectname = opsChooserApp.project.get('name');
                }
            }

            // activate project
            opsChooserApp.trigger('projects:initialize', projectname);

            $(notifybox).qnotify('Database imported successfully');

        });

    },

    dataurl: function() {
        // produce representation like "data:application/json;base64,ewogICAgImRhdGF..."
        var deferred = $.Deferred();
        this.dump().then(function(backup) {
            var payload = JSON.stringify(backup);
            var content = dataurl.format({data: payload, mimetype: 'application/json', charset: 'utf-8'});
            return deferred.resolve(content);
        });
        return deferred.promise();
    },

    setup_ui: function() {

        var _this = this;

        // permalink
        $('#data-permalink-button').unbind('click');
        $('#data-permalink-button').on('click', function(e) {
            var projectname = opsChooserApp.project.get('name');
            _this.dataurl().then(function(dataurl) {
                var url =
                    '?mode=liveview' +
                    '&context=viewer' +
                    '&project=' + encodeURIComponent(projectname) +
                    '&datasource=review' +
                    '&database=' + encodeURIComponent(dataurl);
                window.open(url);
            });
        });

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

            var notifybox = $(this).parent();


            // sanity checks
            if (file.type != 'application/json') {
                $(notifybox).qnotify('ERROR: File type is ' + file.type + ', but should be application/json', {error: true});
                return;
            }


            var reader = new FileReader();
            reader.onload = function(e) {
                var payload = e.target.result;
                _this.dbimport(payload, notifybox);

            };
            reader.onerror = function(e) {
                $(notifybox).qnotify('ERROR: Could not read file ' + file.name + ', message=' + e.getMessage(), {error: true});
            }
            reader.readAsText(file);

        });

        $('#data-import-button').unbind('dblclick');
        $('#data-import-button').on('dblclick', function(e) {
            $('#data-import-file').click();
        });


        // reset database
        $('#factory-reset-button').unbind('dblclick');
        $('#factory-reset-button').on('dblclick', function(e) {
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
    this.listenTo(this, 'application:ready', function() {
        this.storage.setup_ui();
    });
});
