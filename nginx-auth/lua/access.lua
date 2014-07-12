-- -*- coding: utf-8 -*-
-- (c) 2014 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
--[[

(c) 2013, Stavros Korokithakis
http://www.stavros.io/posts/writing-an-nginx-authentication-module-in-lua/

(c) 2013, phear
https://github.com/phaer/nginx-lua-auth

]]

local isis = require('lib/isis')

-- always permit access to the authentication endpoint
if ngx.var.request_uri == "/auth" then
    return
end

-- TODO: better use request_uri here?
if string.find(ngx.var.uri, "^/login$") ~= nil or string.find(ngx.var.uri, "^/ops/browser/login$") ~= nil then
    return
end

if (string.find(ngx.var.request_uri, "^/fanstatic/.*$") ~= nil or string.find(ngx.var.request_uri, "^/static.*$") ~= nil)
    and string.find(ngx.var.request_uri, "app.min.") == nil then
    return
end

if isis.verify_cookie() then
    return
end

-- Internally rewrite the URL so that we serve
-- /auth/ if there's no valid token.
ngx.log(ngx.INFO, 'Require authentication to "' .. ngx.var.request_uri .. '"')
ngx.exec("/auth")
