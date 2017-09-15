// -*- coding: utf-8 -*-
// (c) 2017 Andreas Motl, Elmyra UG
var os = require('os');
const config = require('./webpack.config');
const webpack = require('webpack');

config.output.filename = '[name].bundle.min.js';
config.plugins.push(

    // https://webpack.js.org/plugins/commons-chunk-plugin/
    new webpack.optimize.CommonsChunkPlugin({
        name: "commons",
        filename: "commons.bundle.min.js",
    }),

    // https://webpack.js.org/plugins/uglifyjs-webpack-plugin/
    new webpack.optimize.UglifyJsPlugin({
        parallel: {
            cache: true,
            workers: os.cpus().length - 1,
        },
        ie8: false,
        sourceMap: true,
        compress: {
            warnings: false,
            properties: true,
            sequences: true,
            dead_code: true,
            conditionals: true,
            comparisons: true,
            evaluate: true,
            booleans: true,
            unused: true,
            loops: true,
            hoist_funs: true,
            cascade: true,
            if_return: true,
            join_vars: true,
            //drop_console: true,
            drop_debugger: true,
            unsafe: true,
            hoist_vars: true,
            negate_iife: true,
            //side_effects: true
        },
        mangle: {
            toplevel: true,
            sort: true,
            eval: true,
            properties: true
        },
        output: {
            comments: false,
        },
    })

);

module.exports = config;
