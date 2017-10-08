// -*- coding: utf-8 -*-
// (c) 2017 Andreas Motl, Elmyra UG
const path = require('path');
const webpack = require('webpack');

// Concepts - Using Third Party Libraries that Are not CJS/AMD/ES6 Modules
// https://github.com/webpack/webpack.js.org/issues/63

const __ui = path.resolve(__dirname, 'patzilla-ui');
const __contextpath = path.resolve(__dirname, 'patzilla', 'navigator', 'static');

module.exports = {

    cache: true,
    devtool: "cheap-source-map",

    context: __contextpath,

    entry: {
        'app-standalone': ['./js/boot/standalone.js'],
        'app-embedded':   ['./js/boot/embedded.js'],
        'app-login':      ['./js/app/login.js'],
        'app-help':       [path.resolve(__ui, 'navigator', 'app', 'help')],
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
            // Do these to expose their symbols to the template namespace
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
                test: /\.html$/,
                loader: 'underscore-template-loader',
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

            'patzilla.app.main':                             path.resolve(__contextpath, 'js', 'app', 'main.js'),
            'patzilla.app.ui':                               path.resolve(__contextpath, 'js', 'app', 'ui.js'),
            'patzilla.app.config':                           path.resolve(__contextpath, 'js', 'config.js'),
            'patzilla.app.application':                      path.resolve(__contextpath, 'js', 'app', 'application.js'),
            'patzilla.views.ops':                            path.resolve(__contextpath, 'js', 'app', 'views', 'ops.js'),

            'patzilla.access.depatech':                      path.resolve(__ui, 'access', 'depatech'),
            'patzilla.access.depatisnet':                    path.resolve(__ui, 'access', 'depatisnet'),
            'patzilla.access.epo.ops':                       path.resolve(__ui, 'access', 'epo-ops'),
            'patzilla.access.ificlaims':                     path.resolve(__ui, 'access', 'ificlaims'),

            'patzilla.navigator.app.layout':                 path.resolve(__ui, 'navigator', 'app', 'layout'),
            'patzilla.navigator.style':                      path.resolve(__ui, 'navigator', 'style'),
            'patzilla.navigator.util.linkmaker':             path.resolve(__ui, 'navigator', 'util', 'linkmaker'),
            'patzilla.navigator.util.patentnumbers':         path.resolve(__ui, 'navigator', 'util', 'patentnumbers'),

            'patzilla.navigator.components.analytics':       path.resolve(__ui, 'navigator', 'components', 'analytics'),
            'patzilla.navigator.components.basket':          path.resolve(__ui, 'navigator', 'components', 'basket'),
            'patzilla.navigator.components.comment':         path.resolve(__ui, 'navigator', 'components', 'comment'),
            'patzilla.navigator.components.crawler':         path.resolve(__ui, 'navigator', 'components', 'crawler'),
            'patzilla.navigator.components.document':        path.resolve(__ui, 'navigator', 'components', 'document'),
            'patzilla.navigator.components.export':          path.resolve(__ui, 'navigator', 'components', 'export'),
            'patzilla.navigator.components.hotkeys':         path.resolve(__ui, 'navigator', 'components', 'hotkeys'),
            'patzilla.navigator.components.keywords':        path.resolve(__ui, 'navigator', 'components', 'keywords'),
            'patzilla.navigator.components.opaquelinks':     path.resolve(__ui, 'navigator', 'components', 'opaquelinks'),
            'patzilla.navigator.components.pagination':      path.resolve(__ui, 'navigator', 'components', 'pagination'),
            'patzilla.navigator.components.permalink':       path.resolve(__ui, 'navigator', 'components', 'permalink'),
            'patzilla.navigator.components.project':         path.resolve(__ui, 'navigator', 'components', 'project'),
            'patzilla.navigator.components.querybuilder':    path.resolve(__ui, 'navigator', 'components', 'querybuilder'),
            'patzilla.navigator.components.reading':         path.resolve(__ui, 'navigator', 'components', 'reading'),
            'patzilla.navigator.components.results-dialog':  path.resolve(__ui, 'navigator', 'components', 'results-dialog'),
            'patzilla.navigator.components.results-tabular': path.resolve(__ui, 'navigator', 'components', 'results-tabular'),
            'patzilla.navigator.components.storage':         path.resolve(__ui, 'navigator', 'components', 'storage'),
            'patzilla.navigator.components.viewport':        path.resolve(__ui, 'navigator', 'components', 'viewport'),
            'patzilla.navigator.components.waypoints':       path.resolve(__ui, 'navigator', 'components', 'waypoints'),

            'patzilla.util.common':                          path.resolve(__ui, 'util', 'common'),
            'patzilla.util.jquery':                          path.resolve(__ui, 'util', 'jquery'),
            'patzilla.util.underscore':                      path.resolve(__ui, 'util', 'underscore'),
            'patzilla.util.issuereporter':                   path.resolve(__ui, 'util', 'issuereporter'),

            'patzilla.lib.bs3_list_group':                   path.resolve(__ui, 'lib', 'bs3-list-group'),
            'patzilla.lib.marionette-modalregion':           path.resolve(__ui, 'lib', 'marionette-modalregion'),
            'patzilla.lib.radioplus':                        path.resolve(__ui, 'lib', 'radioplus'),

        }
    },

    plugins: [

        // https://webpack.js.org/plugins/provide-plugin/
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
