// -*- coding: utf-8 -*-
// (c) 2017-2018 Andreas Motl <andreas.motl@ip-tools.org>
const config = require('./webpack.config');
const webpack = require('webpack');
const WebpackNotifierPlugin = require('webpack-notifier');

// https://www.npmjs.com/package/sourcemapped-stacktrace
// https://webpack.js.org/configuration/devtool/
// https://webpack.js.org/plugins/source-map-dev-tool-plugin/
// https://github.com/webpack/webpack/issues/5681#issuecomment-345861733

// This is safe wrt. error handling in Chrome
config.devtool = 'cheap-source-map';

// This is fast, but messes up error handling, at least in Chrome
//config.devtool = 'cheap-module-eval-source-map';

//config.devtool = 'cheap-module-inline-source-map';
//config.devtool = 'eval-cheap-module-source-map';


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

    // https://webpack.js.org/plugins/define-plugin/
    new webpack.DefinePlugin({
        PRODUCTION: JSON.stringify(false),
    }),

    // https://www.npmjs.com/package/webpack-notifier
    new WebpackNotifierPlugin()

);

module.exports = config;
