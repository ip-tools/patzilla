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
// https://webpack.js.org/configuration/devtool/
// https://webpack.js.org/plugins/source-map-dev-tool-plugin/
config.devtool = "source-map";

// Apply code splitting
// https://webpack.js.org/guides/code-splitting/
// https://gist.github.com/sokra/1522d586b8e5c0f5072d7565c2bee693
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

    // TODO: Serve static .gz files via Nginx
    // https://github.com/webpack-contrib/compression-webpack-plugin
    // https://github.com/zeit/next.js/issues/1446#issuecomment-317359011
    // https://medium.com/smartboxtv-engineering/optimizing-loading-time-for-big-react-apps-cf13bbf63c57
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
