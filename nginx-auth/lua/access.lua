-- -*- coding: utf-8 -*-
-- (c) 2014 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
--[[

(c) 2013, Stavros Korokithakis
http://www.stavros.io/posts/writing-an-nginx-authentication-module-in-lua/

(c) 2013, phear
https://github.com/phaer/nginx-lua-auth

]]

local cjson = require('cjson')
local isis = require('lib/isis')

local request_uri = ngx.var.request_uri
local static_resource = request_uri:find("^/fanstatic/.*$") or request_uri:find("^/static.*$")


-- ------------------------------------------
--  route firewall (whitelist)
-- ------------------------------------------

-- always permit access to the authentication endpoint
if request_uri == "/auth" then
    return
end

-- TODO: better use request_uri here?
if request_uri:find("^/login.*$") then
    return
end

if static_resource and not request_uri:find("^/static/js/app.*$") then
    return
end


-- ------------------------------------------
--  verify cookie
-- ------------------------------------------

if isis.verify_cookie() then
    return
end


-- ------------------------------------------
--  send proper '401 Unauthorized' response
-- ------------------------------------------

if static_resource then
    ngx.header.content_type = 'text/plain'
    ngx.status = ngx.HTTP_UNAUTHORIZED
    ngx.say('401 Unauthorized')
    ngx.exit(ngx.status)
end

-- On API requests, respond with proper error json if cookie could not be verified
if ngx.var.request_uri:find("^/api/.*$") then

    -- TODO: prefer window.location.href over ngx.var.http_referer
    local login_args = ngx.encode_args({came_from=ngx.var.http_referer})
    local error = {
        status='error',
        errors={{
            location    = 'Authentication subsystem',
            name        = 'access-denied',
            description = {
                url =           ngx.var.request_uri,
                status_code =   '401',
                reason =        'Unauthorized',
                headers =       {date = ngx.utctime() .. ' UTC'},
                content =       'Access to this resource was denied, the authentication token might have expired. ' ..
                                '&nbsp;&nbsp;' ..
                                '<a href="/login?' .. login_args .. '" role="button" class="btn">Sign in again...</a>',
            },
        }}
    }
    local payload = cjson.encode(error)

    ngx.header.content_type = 'application/json'
    ngx.status = ngx.HTTP_UNAUTHORIZED
    ngx.say(payload)
    ngx.exit(ngx.status)
end

-- For all other requests, rewrite the URL so that we serve /auth if there's no valid token.
ngx.log(ngx.INFO, 'Require authentication to "' .. ngx.var.request_uri .. '"')
return ngx.exec("/auth")
