-- -*- coding: utf-8 -*-
-- (c) 2014 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
--[[

(c) 2013, Stavros Korokithakis
http://www.stavros.io/posts/writing-an-nginx-authentication-module-in-lua/

(c) 2013, phear
https://github.com/phaer/nginx-lua-auth

]]

local config = require('config')
local util = require('lib/util')
local isis = require('lib/isis')

headers = ngx.req.get_headers()

-- TODO: maybe combine both modes
-- http://www.peej.co.uk/articles/http-auth-with-html-forms.html
-- http://stackoverflow.com/questions/5507234/how-to-use-basic-auth-and-jquery-and-ajax
-- https://github.com/fiznool/backbone.basicauth

if config.auth.mode == 'basic-auth' then

    local username, password = util.get_basic_credentials()
    local user = isis.authenticate_user(config.auth.mode, username, password)

    if user then
        isis.set_cookie(user)
        ngx.header.content_type = 'text/html'
        ngx.say("<html><head><script>location.reload()</script></head></html>")
    else
        ngx.header.content_type = 'text/plain'
        ngx.header.www_authenticate = 'Basic realm=""'
        ngx.status = ngx.HTTP_UNAUTHORIZED
        ngx.say('401 Unauthorized')
    end

elseif config.auth.mode == 'login-form' then

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

        local user = isis.authenticate_user(config.auth.mode, args.username, args.password)

        if user then
            isis.set_cookie(user)

            -- TODO: remember me

            local referer_path, referer_args = util.decode_referer()
            local redirect_uri = referer_args.came_from or '/'
            if args.came_from and args.came_from ~= '' then
                redirect_uri = args.came_from
            end
            ngx.log(ngx.WARN, 'Redirecting back to ' .. redirect_uri)
            ngx.redirect(redirect_uri)

        else
            local referer_path, referer_args = util.decode_referer()
            local redirect_uri = util.get_uri(referer_path, referer_args, {username=args.username, error='true'})
            ngx.log(ngx.WARN, 'Redirecting back to ' .. redirect_uri)
            ngx.redirect(redirect_uri)
        end

    end

else

    ngx.header.content_type = 'text/plain'
    local description = 'Reason: Authentication layer does not implement mode "' .. config.auth.mode .. '".'
    ngx.say('Internal Server Error' .. '\n\n' .. description)
    ngx.exit(500)

end
