-- -*- coding: utf-8 -*-
-- (c) 2014 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
--[[

(c) 2013, Stavros Korokithakis
http://www.stavros.io/posts/writing-an-nginx-authentication-module-in-lua/

(c) 2013, phear
https://github.com/phaer/nginx-lua-auth

]]

local config = require('config')
local users = config.users

function authenticate_user(mode, username, password)

    if users[username] ~= password then
        log_auth_outcome(mode, false, username)
        return
    end

    log_auth_outcome(mode, true, username)
    return username
end

function log_auth_outcome(mode, success, username)
    local success_string = success and 'succeeded' or 'failed'
    ngx.log(ngx.INFO, 'Authentication of user "' .. username .. '" ' .. success_string .. ' (mode=' .. mode .. ')')
end

function get_basic_credentials()
    local header = headers['Authorization']
    if header == nil or header:find(" ") == nil then
        return
    end

    local divider = header:find(' ')
    if header:sub(0, divider-1) ~= 'Basic' then
        return
    end

    local auth = ngx.decode_base64(header:sub(divider+1))
    if auth == nil or auth:find(':') == nil then
        return
    end

    divider = auth:find(':')
    local user = auth:sub(0, divider-1)
    local pass = auth:sub(divider+1)

    return user, pass
end

function set_cookie()

    local expires_after = config.auth.cookie_expiration

    local expiration = ngx.time() + expires_after
    local signature = ngx.encode_base64(ngx.hmac_sha1(config.auth.hmac_secret, tostring(expiration)))
    local token = expiration .. ":" .. signature
    local cookie = config.auth.cookie_name .. "=" .. token .. "; "
    -- @TODO: Don't include subdomains
    cookie = cookie .. "Path=/; "
    -- cookie = cookie .. "Domain=" .. ngx.var.server_name .. "; "
    cookie = cookie .. "Expires=" .. ngx.cookie_time(expiration) .. "; "
    cookie = cookie .. "Max-Age=" .. expires_after .. "; "
    cookie = cookie .. "HttpOnly"
    ngx.header['Set-Cookie'] = cookie
end

function verify_cookie()

    local var_name = "cookie_" .. config.auth.cookie_name
    local cookie = ngx.var[var_name]

    -- Check that the cookie exists.
    if cookie ~= nil and cookie:find(":") ~= nil then
        -- If there's a cookie, split off the HMAC signature
        -- and timestamp.
        local divider = cookie:find(":")
        local hmac = ngx.decode_base64(cookie:sub(divider+1))
        local timestamp = cookie:sub(0, divider-1)

        -- Verify that the signature is valid.
        if ngx.hmac_sha1(config.auth.hmac_secret, timestamp) == hmac and tonumber(timestamp) >= ngx.time() then

            -- TODO: propagate userid/username to upstream service using http headers
            -- TODO: automatic token renewal

            return true
        end
    end

    return false
end

return {
    authenticate_user=authenticate_user,
    get_basic_credentials=get_basic_credentials,
    set_cookie=set_cookie,
    verify_cookie=verify_cookie,
    decode_referer=decode_referer,
}
