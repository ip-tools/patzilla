// -*- coding: utf-8 -*-
/*
 * module for dealing with dataurls
 * see also: http://en.wikipedia.org/wiki/Data_URI_scheme
 *
 * (c) 2013 Brian J Brennan
 * https://github.com/brianloveswords/dataurl
 *
 * (c) 2014 Andreas Motl, Elmyra UG
 *
 * Changes:
 * 2014-06-13 Stripped down, now also runs on non-node.js, therefore it relies
 *            on the jquery-base64 plugin and stopped supporting streams.
 * 2014-06-15 Add lz-string compression
 *
 */

const REGEX = {
  dataurl: /data:(.*?)(?:;charset=(.*?))?(;base64)?,(.+)/i,
  newlines: /(\r)|(\n)/g
}
const MIME_INDEX = 1;
const CHARSET_INDEX = 2;
const ENCODED_INDEX = 3;
const DATA_INDEX = 4;

function dataurl() {}

function stripNewlines(string) {
  return string.replace(REGEX.newlines, '');
}

function isString(thing) {
  return typeof thing === 'string';
}

function makeHeader(options) {
  var dataUrlTemplate = 'data:' + options.mimetype;
  if (options.charset)
    dataUrlTemplate += ';charset=' + options.charset;
  if (options.encoded !== false)
    dataUrlTemplate += ';base64'
  dataUrlTemplate += ',';
  return dataUrlTemplate;
}

function makeDataUrlSync(header, options) {
  var data = options.data;
  if (options.encoded !== false)
    data = LZString.compressToBase64(data);
  return (header + data);
}

dataurl.convert = function (options) {
  const header = makeHeader(options);
  return makeDataUrlSync(header, options);
};
dataurl.format = dataurl.convert;

dataurl.parse = function (string) {
  var match;
  if (!isString(string))
    return false;
  string = stripNewlines(string);
  if (!(match = REGEX.dataurl.exec(string)))
    return false;
  const encoded = !!match[ENCODED_INDEX];
  const base64 = (encoded ? 'base64' : null);
  var data = match[DATA_INDEX];
  if (encoded !== false)
    data = LZString.decompressFromBase64(data);
  const charset = match[CHARSET_INDEX];
  const mimetype = match[MIME_INDEX] || 'text/plain';
  return {
    mimetype: mimetype,
    charset: charset,
    data: data,
  }
};
