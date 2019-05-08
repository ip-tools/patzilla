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
local util = require('lib/util')

local request_uri = ngx.var.request_uri


-- ------------------------------------------
--  route firewall (whitelist)
-- ------------------------------------------

-- always permit access to ...

-- the authentication endpoint
if request_uri == "/auth" then
    return
end

-- the login form
if request_uri:find("^/login.*$") then
    return
end

-- all static resources
if request_uri:find("^/static.*$") then
    return
end

-- some api endpoints
if request_uri:find("^/api/identity/pwhash.*$") then
    return
end

-- temporarily allow kindcode inquiry
if request_uri:find("^/api/ops/.+/kindcodes$") then
    return
end

-- temporarily allow DPMAregister access
-- e.g. /api/dpma/register/patent/ES2023846
if request_uri:find("^/api/dpma/register/.+$") then
    return
end

-- temporarily allow free embedding
--if request_uri:find("^/embed/.*$") then
--    return
--end

-- "patentview" domains
if ngx.var.host:find("^patentview.*$") or ngx.var.host:find("^viewer.*$") or ngx.var.host:find("^patview.*$") then
    return
end

-- allow /ping endpoints
if request_uri:find("^/ping.*$") then
    return
end

-- allow /api/status endpoints
if request_uri:find("^/api/status.*$") then
    return
end


-- ------------------------------------------
--  handle logout
-- ------------------------------------------
if request_uri:find("^/logout.*$") then
    isis.delete_cookie()
end


-- ------------------------------------------
--  verify cookie
-- ------------------------------------------
local user = isis.verify_cookie()
if user then

    -- permit admin access only to users with tag "staff"
    if request_uri:find("^/admin.*$") or request_uri:find("^/api/admin.*$") then
        if user.tags and util.table_contains(user.tags, 'staff') then
            return
        end
    else
        return
    end
end


-- ------------------------------------------
--  send proper '401 Unauthorized' response
-- ------------------------------------------

-- if request_uri:find("^/static.*$") then
--     ngx.header.content_type = 'text/plain'
--     ngx.status = ngx.HTTP_UNAUTHORIZED
--     ngx.say('401 Unauthorized')
--     ngx.exit(ngx.status)
-- end

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
