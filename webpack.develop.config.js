// -*- coding: utf-8 -*-
// (c) 2017 Andreas Motl, Elmyra UG
const config = require('./webpack.config');
const webpack = require('webpack');
const WebpackNotifierPlugin = require('webpack-notifier');

// https://www.npmjs.com/package/sourcemapped-stacktrace
config.devtool = "source-map";

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
