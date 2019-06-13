// -*- coding: utf-8 -*-
// (c) 2017-2018 Andreas Motl <andreas.motl@ip-tools.org>
const path = require('path');
const webpack = require('webpack');
const CleanWebpackPlugin = require('clean-webpack-plugin');
const LicenseWebpackPlugin = require('license-webpack-plugin').LicenseWebpackPlugin;
var fs = require("fs");

// Concepts - Using Third Party Libraries that Are not CJS/AMD/ES6 Modules
// https://github.com/webpack/webpack.js.org/issues/63

const __ui = path.resolve(__dirname, 'patzilla-ui');
const __contextpath = path.resolve(__dirname, 'patzilla', 'navigator', 'static');

const config = {

    cache: true,

    context: __contextpath,

    entry: {
        'app-standalone': [path.resolve(__ui, 'navigator', 'boot', 'standalone')],
        'app-embedded':   [path.resolve(__ui, 'navigator', 'boot', 'embedded')],
        'app-help':       [path.resolve(__ui, 'navigator', 'app', 'help')],
        'app-login':      [path.resolve(__ui, 'common', 'login')],
        'app-admin':      [path.resolve(__ui, 'common', 'admin')],
    },

    output: {
        path: path.resolve(__contextpath, 'assets'),
        filename: '[name].bundle.js',
        publicPath: '/static/assets/',
    },

    optimization: {
        usedExports: true,

        // https://webpack.js.org/plugins/module-concatenation-plugin/
        //concatenateModules: false,

        // To keep filename consistent between different modes (for example building only)
        occurrenceOrder: true
    },

    // Configure performance budget
    // https://webpack.js.org/configuration/performance/
    // https://github.com/webpack/webpack/issues/3486
    // https://github.com/webpack/webpack/issues/3216
    performance: {
        //hints: false,
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

    plugins: [

        new CleanWebpackPlugin({
            cleanOnceBeforeBuildPatterns: ['**/*', '!README.txt', '!.gitignore'],
        }),

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

        // https://webpack.js.org/plugins/banner-plugin/
        new webpack.BannerPlugin(fs.readFileSync('./webpack.banner.txt', 'utf8')),

        // https://github.com/xz64/license-webpack-plugin
        new LicenseWebpackPlugin({
          perChunkOutput: false,
          stats: {
            warnings: false,
            errors: false
          }
        }),

    ],

    module: {
        rules: [

            // Use Babel for loading own code
            // https://www.npmjs.com/package/babel-loader
            {
                test: /\.tsx?$/,
                exclude: /(node_modules|bower_components)/,
                loaders: [
                    {
                        loader: 'babel-loader',
                        options: { presets: ['env'] },
                    },
                    'ts-loader',
                ],
            },
            {
                test: /\.js$/,
                exclude: /(node_modules|bower_components)/,
                use: [
                    {
                        loader: 'babel-loader',
                        options: {
                            cacheDirectory: true,
                            presets: [
                                // https://babeljs.io/docs/plugins/preset-env/
                                ['env', { modules: false, debug: true }],
                            ],
                            //plugins: ['transform-runtime'],
                        }
                    },
                ]
            },

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

            // https://github.com/jquery/jquery-migrate/issues/273
            {
                test: require.resolve("jquery-migrate"),
                use: "imports-loader?define=>false",
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

            // Disabled in favor of sass-loader, see below.
            /*
            {
                test: /\.css$/,
                use: [
                    'style-loader',
                    'css-loader'
                ]
            },
            */

            // Use Sass loader for using Material Components for the web
            // https://github.com/webpack-contrib/sass-loader
            // https://github.com/material-components/material-components-web
            {
                test: /\.(css|scss)$/,
                use: [

                    // Create style nodes from JS strings
                    "style-loader",

                    // Translate CSS into CommonJS
                    "css-loader",

                    // Compile Sass to CSS, using Node Sass by default
                    {
                        loader: "sass-loader",
                        options: {
                            includePaths: ['./node_modules']
                        }
                    },

                ],
            },

            {
                test: /\.(woff|woff2|eot|ttf|otf)$/,
                use: [
                    'file-loader'
                ]
            },
            {
                test: /\.(png|svg|jpg|gif|swf|ico)$/,
                use: [
                    'file-loader'
                ]
            },
            {
                test: /\.html$/,
                loader: 'underscore-template-loader',
            },
            {
                test: /\.modernizrrc.js$/,
                loader: "modernizr-loader"
            },
            {
                test: /\.modernizrrc(\.json)?$/,
                loader: "modernizr-loader!json-loader"
            },

            /*
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
            path.resolve(__ui, 'vendor', 'lib'),
            path.resolve(__ui, 'vendor', 'widget'),
        ],

        extensions: [".ts", ".tsx", ".js", ".jsx", ".min.js", ".json", ".css", ".scss"],

        alias: {

            'patzilla.navigator.app.main':                   path.resolve(__ui, 'navigator', 'app', 'main'),
            'patzilla.navigator.app.config':                 path.resolve(__ui, 'navigator', 'app', 'config'),
            'patzilla.navigator.app.application':            path.resolve(__ui, 'navigator', 'app', 'application'),

            'patzilla.navigator.app.layout':                 path.resolve(__ui, 'navigator', 'app', 'layout'),
            'patzilla.navigator.app.ui':                     path.resolve(__ui, 'navigator', 'app', 'ui'),
            'patzilla.navigator.app.results':                path.resolve(__ui, 'navigator', 'app', 'results'),
            'patzilla.navigator.app.document':               path.resolve(__ui, 'navigator', 'app', 'document'),
            'patzilla.navigator.style':                      path.resolve(__ui, 'navigator', 'style'),
            'patzilla.navigator.util.linkmaker':             path.resolve(__ui, 'navigator', 'util', 'linkmaker'),
            'patzilla.navigator.util.patentnumbers':         path.resolve(__ui, 'navigator', 'util', 'patentnumbers'),

            'patzilla.navigator.components.analytics':       path.resolve(__ui, 'navigator', 'components', 'analytics'),
            'patzilla.navigator.components.basket':          path.resolve(__ui, 'navigator', 'components', 'basket'),
            'patzilla.navigator.components.comment':         path.resolve(__ui, 'navigator', 'components', 'comment'),
            'patzilla.navigator.components.crawler':         path.resolve(__ui, 'navigator', 'components', 'crawler'),
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
            'patzilla.navigator.components.stack':           path.resolve(__ui, 'navigator', 'components', 'stack'),
            'patzilla.navigator.components.storage':         path.resolve(__ui, 'navigator', 'components', 'storage'),
            'patzilla.navigator.components.viewport':        path.resolve(__ui, 'navigator', 'components', 'viewport'),
            'patzilla.navigator.components.waypoints':       path.resolve(__ui, 'navigator', 'components', 'waypoints'),
            'patzilla.navigator.components.nataraja':        path.resolve(__ui, 'navigator', 'components', 'nataraja'),

            'patzilla.access.depatech':                      path.resolve(__ui, 'access', 'depatech'),
            'patzilla.access.depatisnet':                    path.resolve(__ui, 'access', 'depatisnet'),
            'patzilla.access.epo.ops':                       path.resolve(__ui, 'access', 'epo-ops'),
            'patzilla.access.ificlaims':                     path.resolve(__ui, 'access', 'ificlaims'),
            'patzilla.access.sip':                           path.resolve(__ui, 'access', 'sip'),

            'patzilla.lib.es6':                              path.resolve(__ui, 'lib', 'es6'),
            'patzilla.lib.util':                             path.resolve(__ui, 'lib', 'util'),
            'patzilla.lib.jquery':                           path.resolve(__ui, 'lib', 'jquery'),
            'patzilla.lib.underscore':                       path.resolve(__ui, 'lib', 'underscore'),
            'patzilla.lib.backbone':                         path.resolve(__ui, 'lib', 'backbone'),
            'patzilla.lib.marionette':                       path.resolve(__ui, 'lib', 'marionette'),
            'patzilla.lib.radioplus':                        path.resolve(__ui, 'lib', 'radioplus'),
            'patzilla.lib.hero-checkbox':                    path.resolve(__ui, 'lib', 'hero-checkbox'),
            'patzilla.lib.mdc.material-icons':               path.resolve(__ui, 'lib', 'mdc', 'material-icons'),
            'patzilla.lib.mdc.snackbar':                     path.resolve(__ui, 'lib', 'mdc', 'snackbar'),
            'patzilla.lib.mui.dialog':                       path.resolve(__ui, 'lib', 'mui', 'dialog'),
            'patzilla.common.issuereporter':                 path.resolve(__ui, 'common', 'issuereporter'),

            modernizr$:                                      path.resolve(__ui, 'vendor', '.modernizrrc'),
            'backbone': path.join(__dirname, 'node_modules', 'backbone', 'backbone.js'),
            'underscore': path.join(__dirname, 'node_modules', 'underscore', 'underscore.js')

        }
    },

};

module.exports = config;
