-- -*- coding: utf-8 -*-
-- (c) 2014 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
--[[

(c) 2013, Stavros Korokithakis
http://www.stavros.io/posts/writing-an-nginx-authentication-module-in-lua/

(c) 2013, phear
https://github.com/phaer/nginx-lua-auth

]]

local cjson = require('cjson')
local config = require('config')
local util = require('lib/util')

function authenticate_user(mode, username, password)

    ngx.req.set_header('Content-Type', 'application/json')
    local response = ngx.location.capture(
        '/api/identity/auth',
        { method = ngx.HTTP_POST, body = cjson.encode({username=username, password=password}) }
    )

    if response.status == 200 then
        log_auth_outcome(mode, true, username)
        return cjson.decode(response.body)
    else
        log_auth_outcome(mode, false, username)
    end

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

-- TODO: encode_token(), decode_token()
-- TODO: put username and/or userid into token

--[[
TODO: maybe use Jwt for token encoding, see also:
- https://github.com/Olivine-Labs/lua-jwt
- https://github.com/webscriptio/lib/blob/master/jwt.lua
]]

function encode_token(user, timestamp)
    local data = util.deepcopy(user)
    local payload = cjson.encode(data)
    local hmac = ngx.hmac_sha1(config.auth.hmac_secret, payload)

    local payload_wire = ngx.encode_base64(payload)
    local signature = ngx.encode_base64(hmac)
    local token = timestamp .. ":" .. payload_wire .. ":" .. signature
    return token
end

function decode_token(token)
    -- Split token into timestamp, payload and HMAC signature

    local timestamp, payload_wire, signature = token:match('(.+):(.+):(.+)')
    timestamp = tonumber(timestamp)

    local payload = ngx.decode_base64(payload_wire)
    local hmac = ngx.decode_base64(signature)

    local data = cjson.decode(payload)

    local response = {
        meta = {
            hmac = hmac,
            timestamp = timestamp,
        },
        data = data
    }
    return response
end

function set_cookie(user)
    -- set a session cookie: https://en.wikipedia.org/wiki/HTTP_cookie#Session_cookie
    local expires_after = config.auth.cookie_expiration
    local expiration = ngx.time() + expires_after
    local token = encode_token(user, expiration)

    local cookie = config.auth.cookie_name .. "=" .. token .. "; "
    -- @TODO: Don't include subdomains
    cookie = cookie .. "Path=/; "
    -- cookie = cookie .. "Domain=" .. ngx.var.server_name .. "; "

    -- don't use expiry when setting session cookies
    --cookie = cookie .. "Expires=" .. ngx.cookie_time(expiration) .. "; "
    --cookie = cookie .. "Max-Age=" .. expires_after .. "; "

    -- https://en.wikipedia.org/wiki/HTTP_cookie#Secure_cookie
    if ngx.var.scheme == 'https' then
        cookie = cookie .. "Secure; "
    end

    -- https://en.wikipedia.org/wiki/HTTP_cookie#HttpOnly_cookie
    cookie = cookie .. "HttpOnly"
    ngx.header['Set-Cookie'] = cookie
end

function delete_cookie()
    local cookie = config.auth.cookie_name .. "=; "
    ngx.header['Set-Cookie'] = cookie
end

function verify_cookie()

    local var_name = "cookie_" .. config.auth.cookie_name
    local token = ngx.var[var_name]

    -- Check that the cookie exists.
    if token ~= nil and token:find(":") ~= nil then

        -- If there's a cookie, decode it.
        local payload = decode_token(token)
        local timestamp = payload.meta.timestamp
        local user = payload.data

        -- user must be present in cookie
        if not user or user == cjson.null then
            ngx.log(ngx.WARN, 'user is empty')
            return
        end

        -- Verify that the signature is valid and the token did not expire.
        local ttl = timestamp - ngx.time()

        -- TODO: prevent timing attacks, see also:
        --[[
        http://codahale.com/a-lesson-in-timing-attacks/
        http://emerose.com/timing-attacks-explained
        http://seb.dbzteam.org/crypto/python-oauth-timing-hmac.pdf
        http://carlos.bueno.org/2011/10/timing.html
        http://www.levigross.com/2014/02/07/constant-time-comparison-functions-in-python-haskell-clojure-java-etc/
        see also: elmyra.web.identity
        ]]

        if ttl >= 0 and encode_token(user, timestamp) == token then

            -- propagate userid/username to upstream service via http headers
            ngx.header['X-User-Id'] = user.userid
            ngx.header['X-User-Username'] = user.username
            ngx.header['X-User-Fullname'] = user.fullname
            if user.tags then
                ngx.header['X-User-Tags'] = cjson.encode(user.tags)
            end

            -- automatic token renewal
            if ttl <= config.auth.cookie_renewal then
                ngx.log(ngx.INFO, 'Renewed cookie')
                set_cookie(user)
            end

            return user
        end
    end

end

return {
    authenticate_user=authenticate_user,
    get_basic_credentials=get_basic_credentials,
    set_cookie=set_cookie,
    delete_cookie=delete_cookie,
    verify_cookie=verify_cookie,
    decode_referer=decode_referer,
}
