-- -*- coding: utf-8 -*-
-- (c) 2014 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
--[[

(c) 2013, Stavros Korokithakis
http://www.stavros.io/posts/writing-an-nginx-authentication-module-in-lua/

(c) 2013, phear
https://github.com/phaer/nginx-lua-auth

]]

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
    local expires_after = 3600
    local expiration = ngx.time() + expires_after
    local signature = ngx.encode_base64(ngx.hmac_sha1(ngx.var.lua_auth_secret, tostring(expiration)))
    local token = expiration .. ":" .. signature
    local cookie = "Auth=" .. token .. "; "
    -- @TODO: Don't include subdomains
    cookie = cookie .. "Path=/; "
    -- cookie = cookie .. "Domain=" .. ngx.var.server_name .. "; "
    cookie = cookie .. "Expires=" .. ngx.cookie_time(expiration) .. "; "
    cookie = cookie .. "Max-Age=" .. expires_after .. "; "
    cookie = cookie .. "HttpOnly"
    ngx.header['Set-Cookie'] = cookie
end

function decode_referer()
    return decode_uri(ngx.var.http_referer)
end

function decode_uri(uri)
    local path, args = string.match(uri, '(.+)?(.+)')
    if not path then
        path = uri
    end
    if args then
        args = ngx.decode_args(args)
    else
        args = {}
    end
    --ngx.log(ngx.ERR, 'args: ' .. args.came_from)
    return path, args
end

function table_merge(target, new)
    for k,v in pairs(new) do target[k] = v end
end

-- http://lua-users.org/wiki/CopyTable
function deepcopy(orig)
    local orig_type = type(orig)
    local copy
    if orig_type == 'table' then
        copy = {}
        for orig_key, orig_value in next, orig, nil do
            copy[deepcopy(orig_key)] = deepcopy(orig_value)
        end
        setmetatable(copy, deepcopy(getmetatable(orig)))
    else -- number, string, boolean, etc
        copy = orig
    end
    return copy
end

function get_uri(path, args, args_more)
    local uri_args = deepcopy(args)
    table_merge(uri_args, args_more)
    return path .. '?' .. ngx.encode_args(uri_args)
end

return {
    get_basic_credentials=get_basic_credentials,
    set_cookie=set_cookie,
    decode_referer=decode_referer,
}
