// -*- coding: utf-8 -*-
// (c) 2017 Andreas Motl, Elmyra UG
var os = require('os');
const config = require('./webpack.config');
const webpack = require('webpack');
const UglifyJsPlugin = require('uglifyjs-webpack-plugin');
const CompressionPlugin = require("compression-webpack-plugin");

// Signal minified resource names
config.output.filename = '[name].bundle.min.js';

// https://www.npmjs.com/package/sourcemapped-stacktrace
config.devtool = "source-map";

config.optimization.splitChunks = {
    cacheGroups: {
        commons: {
            //test: /[\\/]node_modules[\\/]/,
            name: "commons",
            filename: "commons.bundle.min.js",
            chunks: "initial",
            minChunks: 3,
            reuseExistingChunk: true,
        }
    }
};

config.plugins.push(

    // https://github.com/webpack-contrib/compression-webpack-plugin
    /*
    new CompressionPlugin({
        cache: true,
    })
    */

);


config.optimization.minimizer = [

    // https://webpack.js.org/plugins/uglifyjs-webpack-plugin/
    new UglifyJsPlugin({
        sourceMap: true,
        cache: true,
        parallel: true,
        /*
        uglifyOptions: {
            ie8: false,
            compress: {
                passes: 2,
                //toplevel: true,
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
                hoist_props: true,
                hoist_vars: true,
                //cascade: true,
                if_return: true,
                join_vars: true,
                drop_console: false,
                drop_debugger: true,
                //unsafe: true,
                negate_iife: true,
                //side_effects: true
            },
            mangle: {
                //toplevel: true,
                //sort: true,
                //eval: true,
                properties: true
            },
            output: {
                comments: false,
                beautify: false,
            },
        },
        */
    })

];


module.exports = config;
