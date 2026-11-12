// -*- coding: utf-8 -*-
// (c) 2017-2018 Andreas Motl <andreas.motl@ip-tools.org>
var os = require('os');
const config = require('./webpack.config');
const webpack = require('webpack');
const MinimizerPlugin = require('minimizer-webpack-plugin');
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

    // https://webpack.js.org/plugins/define-plugin/
    new webpack.DefinePlugin({
        PRODUCTION: JSON.stringify(true),
    })

);

// https://webpack.js.org/plugins/minimizer-webpack-plugin/
// https://www.npmjs.com/package/minimizer-webpack-plugin
config.optimization.minimize = true;
config.optimization.minimizer = [
    new MinimizerPlugin({
        parallel: true,
    }),
];

module.exports = config;
