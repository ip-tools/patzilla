// -*- coding: utf-8 -*-
// (c) 2017 Andreas Motl, Elmyra UG
const config = require('./webpack.config');
const webpack = require('webpack');
const WebpackNotifierPlugin = require('webpack-notifier');

config.plugins.push(

    // https://www.npmjs.com/package/webpack-notifier
    new WebpackNotifierPlugin(),

    // https://webpack.js.org/plugins/commons-chunk-plugin/
    new webpack.optimize.CommonsChunkPlugin({
        name: "commons",
        filename: "commons.bundle.js",
    })

);

module.exports = config;
