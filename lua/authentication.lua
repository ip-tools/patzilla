-- -*- coding: utf-8 -*-
-- (c) 2014 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
--[[

(c) 2013, Stavros Korokithakis
http://www.stavros.io/posts/writing-an-nginx-authentication-module-in-lua/

(c) 2013, phear
https://github.com/phaer/nginx-lua-auth

]]

local config = require('config')
local util = require('util')
local users = config.users

headers = ngx.req.get_headers()

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

if config.authmode == 'basic-auth' then

    local username, password = util.get_basic_credentials()
    local user = authenticate_user(config.authmode, username, password)

    if user then
        util.set_cookie()
        ngx.header.content_type = 'text/html'
        ngx.say("<html><head><script>location.reload()</script></head></html>")
    else
        ngx.header.content_type = 'text/plain'
        ngx.header.www_authenticate = 'Basic realm=""'
        ngx.status = ngx.HTTP_UNAUTHORIZED
        ngx.say('401 Access Denied')
    end

elseif config.authmode == 'login-form' then

    local http_method = ngx.req.get_method()

    if http_method == 'GET' then

        -- v1
        --ngx.exec("/login")

        -- v2
        local came_from = ngx.var.request_uri
        local redirect_uri = '/login'
        if came_from and came_from ~= '/' then
            redirect_uri = redirect_uri .. '?' .. ngx.encode_args({came_from=came_from})
        end
        ngx.redirect(redirect_uri)

    elseif http_method == 'POST' then
        local args, err = ngx.req.get_post_args()

        local user = authenticate_user(config.authmode, args.username, args.password)

        if user then
            set_cookie()

            -- TODO: remember me

            local referer_path, referer_args = util.decode_referer()
            local redirect_uri = referer_args.came_from or '/'
            ngx.log(ngx.WARN, 'Redirecting back to ' .. redirect_uri)
            ngx.redirect(redirect_uri)

        else
            local referer_path, referer_args = util.decode_referer()
            local redirect_uri = get_uri(referer_path, referer_args, {username=args.username, error='true'})
            ngx.log(ngx.WARN, 'Redirecting back to ' .. redirect_uri)
            ngx.redirect(redirect_uri)
        end

    end

else

    ngx.header.content_type = 'text/plain'
    local description = 'Reason: Authentication layer does not implement authmode "' .. config.authmode .. '".'
    ngx.say('Internal Server Error' .. '\n\n' .. description)
    ngx.exit(500)

end
