// -*- coding: utf-8 -*-
// (c) 2017 Andreas Motl, Elmyra UG
const config = require('./webpack.config');
const webpack = require('webpack');
const WebpackNotifierPlugin = require('webpack-notifier');

// https://www.npmjs.com/package/sourcemapped-stacktrace
// https://webpack.js.org/configuration/devtool/
// https://webpack.js.org/plugins/source-map-dev-tool-plugin/
//config.devtool = 'cheap-source-map';
config.devtool = 'cheap-module-eval-source-map',
//config.devtool = 'eval-cheap-module-source-map',
//config.devtool = 'cheap-module-inline-source-map',

// Apply code splitting
// https://webpack.js.org/guides/code-splitting/
// https://gist.github.com/sokra/1522d586b8e5c0f5072d7565c2bee693
config.optimization.splitChunks = {
    cacheGroups: {
        commons: {
            //test: /[\\/]node_modules[\\/]/,
            name: "commons",
            filename: "commons.bundle.js",
            chunks: "initial",
            minChunks: 3,
            reuseExistingChunk: true,
        }
    }

};

config.optimization.minimizer = [];

config.plugins.push(

    // https://www.npmjs.com/package/webpack-notifier
    new WebpackNotifierPlugin()

);

module.exports = config;
