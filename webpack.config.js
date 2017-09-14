// -*- coding: utf-8 -*-
// (c) 2017 Andreas Motl, Elmyra UG

const path = require('path');
const webpack = require('webpack');

// Concepts - Using Third Party Libraries that Are not CJS/AMD/ES6 Modules
// https://github.com/webpack/webpack.js.org/issues/63

const __contextpath = path.resolve(__dirname, 'patzilla', 'navigator', 'static');

module.exports = {

    context: __contextpath,

    entry: {
        'app-standalone': ['./js/boot/standalone.js'],
        'app-embedded':   ['./js/boot/embedded.js'],
        'app-login':      ['./js/app/login.js'],
        'app-help':       ['./widget/help/help.js'],
    },

    amd: {
        'jquery': true,
        'backbone': true,
        'backbone.marionette': true,
        'classie': true,
        'localforage.nopromises': true,
        'localforage.backbone': true,
        'backbone-relational': true,
    },

    output: {
        path: path.resolve(__contextpath, 'assets'),
        filename: '[name].bundle.js',
        publicPath: '/static/assets/',
    },

    module: {
        rules: [
            {
                test: require.resolve('jquery'),
                use: [
                    {
                        loader: 'expose-loader',
                        options: 'jQuery',
                    },
                    {
                        loader: 'expose-loader',
                        options: '$',
                    },
                ],
            },
            {
                test: require.resolve('humanize-plus'),
                use: [
                    {
                        loader: 'expose-loader',
                        options: 'Humanize',
                    },
                ],
            },
            {
                test: /\.css$/,
                use: [
                    'style-loader',
                    'css-loader'
                ]
            },
            {
                test: /\.(woff|woff2|eot|ttf|otf)$/,
                use: [
                    'file-loader'
                ]
            },
            {
                test: /\.(png|svg|jpg|gif|swf)$/,
                use: [
                    'file-loader'
                ]
            },
            {
                test: /js\/app\/lib\/util2\.js$/,
                use: [ 'script-loader' ]
            },
            {
                test: /js\/app\/core\.js$/,
                use: [ 'script-loader' ]
            },
            /*
             {
                 test: /\.js$/,
                 exclude: /node_modules/,
                 use: [
                     { loader: 'ng-annotate-loader', options: { es6: true } },
                     { loader: 'babel-loader', options: { presets: ['env'] } },
                 ]
             },
              {
                  test: /\.html$/,
                  loader: 'underscore-template-loader'
              },
            {
                test: /\.(csv|tsv)$/,
                use: [
                    'csv-loader'
                ]
            },
            {
                test: /\.xml$/,
                use: [
                    'xml-loader'
                ]
            }
            */
        ]
    },

    resolve: {
        // Options for resolving module requests (does not apply to resolving to loaders)

        // Directories where to look for modules
        modules: [
            "node_modules",
            path.resolve(__contextpath, 'js', 'lib'),
            path.resolve(__contextpath, 'widget'),
        ],

        extensions: [".js", ".jsx", ".min.js", ".json", ".css"],

        alias: {
            'patzilla.app.main':                    path.resolve(__contextpath, 'js', 'app', 'main.js'),
            'patzilla.app.core':                    path.resolve(__contextpath, 'js', 'app', 'core.js'),
            'patzilla.app.ui':                      path.resolve(__contextpath, 'js', 'app', 'ui.js'),
            'patzilla.backend.fields':              path.resolve(__contextpath, 'js', 'app', 'ops-sdk.js'),
            'patzilla.app.config':                  path.resolve(__contextpath, 'js', 'config.js'),
            'patzilla.app.application':             path.resolve(__contextpath, 'js', 'app', 'application.js'),
            'patzilla.util.issuereporter':          path.resolve(__contextpath, 'js', 'issue-reporter.js'),
            'patzilla.util.radioplus':              path.resolve(__contextpath, 'js', 'app', 'lib', 'radio-plus.js'),
            'patzilla.util.jplugins':               path.resolve(__contextpath, 'js', 'app', 'lib', 'foundation-plugins.js'),
            'patzilla.util.common':                 path.resolve(__contextpath, 'js', 'app', 'lib', 'util.js'),
            'patzilla.util.linkmaker':              path.resolve(__contextpath, 'js', 'app', 'lib', 'linkmaker.js'),
            'patzilla.util.patentnumbers':          path.resolve(__contextpath, 'js', 'app', 'lib', 'patents.js'),
            'patzilla.models.generic':              path.resolve(__contextpath, 'js', 'app', 'models', 'generic.js'),
            'patzilla.models.search':               path.resolve(__contextpath, 'js', 'app', 'models', '01-search.js'),
            'patzilla.models.results':              path.resolve(__contextpath, 'js', 'app', 'models', '01-results.js'),
            'patzilla.models.ops':                  path.resolve(__contextpath, 'js', 'app', 'models', 'ops.js'),
            'patzilla.models.depatisnet':           path.resolve(__contextpath, 'js', 'app', 'models', 'depatisnet.js'),
            'patzilla.models.ificlaims':            path.resolve(__contextpath, 'js', 'app', 'models', 'ifi.js'),
            'patzilla.models.depatech':             path.resolve(__contextpath, 'js', 'app', 'models', 'depatech.js'),
            'patzilla.views.common':                path.resolve(__contextpath, 'js', 'app', 'views', 'common.js'),
            'patzilla.views.results':               path.resolve(__contextpath, 'js', 'app', 'views', '01-results.js'),
            'patzilla.views.ops':                   path.resolve(__contextpath, 'js', 'app', 'views', 'ops.js'),
            'patzilla.views.pagination':            path.resolve(__contextpath, 'js', 'app', 'views', 'pagination.js'),
            'patzilla.components.analytics':        path.resolve(__contextpath, 'js', 'components', 'analytics.js'),
            'patzilla.components.basket':           path.resolve(__contextpath, 'js', 'components', 'basket.js'),
            'patzilla.components.comment':          path.resolve(__contextpath, 'js', 'components', 'comment.js'),
            'patzilla.components.crawler':          path.resolve(__contextpath, 'js', 'components', 'crawler.js'),
            'patzilla.components.document':         path.resolve(__contextpath, 'js', 'components', 'document.js'),
            'patzilla.components.export':           path.resolve(__contextpath, 'js', 'components', 'export.js'),
            'patzilla.components.hotkeys':          path.resolve(__contextpath, 'js', 'components', 'hotkeys.js'),
            'patzilla.components.keywords':         path.resolve(__contextpath, 'js', 'components', 'keywords.js'),
            'patzilla.components.opaquelinks':      path.resolve(__contextpath, 'js', 'components', 'opaquelinks.js'),
            'patzilla.components.permalink':        path.resolve(__contextpath, 'js', 'components', 'permalink.js'),
            'patzilla.components.project':          path.resolve(__contextpath, 'js', 'components', 'project.js'),
            'patzilla.components.querybuilder':     path.resolve(__contextpath, 'js', 'components', 'querybuilder.js'),
            'patzilla.components.reading':          path.resolve(__contextpath, 'js', 'components', 'reading.js'),
            'patzilla.components.storage':          path.resolve(__contextpath, 'js', 'components', 'storage.js'),
            'patzilla.components.viewport':         path.resolve(__contextpath, 'js', 'components', 'viewport.js'),
            'patzilla.components.waypoints':        path.resolve(__contextpath, 'js', 'components', 'waypoints.js'),
            //Templates: path.resolve(__dirname, 'src/templates/')
        }
    },

    plugins: [
        new webpack.ProvidePlugin({
            '$': 'jquery',
            'jQuery': 'jquery',
            '_': 'underscore',
            '_.str': 'underscore.string',
            '_.string': 'underscore.string',
            'moment': 'moment',
            'Humanize': 'humanize-plus',
            'Backbone': 'backbone',
            'Marionette': 'backbone.marionette',
            'Backbone.Marionette': 'backbone.marionette',
        }),
    ],

};
