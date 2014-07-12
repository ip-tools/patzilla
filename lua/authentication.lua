-- -*- coding: utf-8 -*-
-- (c) 2014 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
--[[

(c) 2013, Stavros Korokithakis
http://www.stavros.io/posts/writing-an-nginx-authentication-module-in-lua/

(c) 2013, phear
https://github.com/phaer/nginx-lua-auth

]]

local config = require('config');
local users = config.users;

headers = ngx.req.get_headers();

function get_user()
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
   if users[user] ~= pass then
      return
   end

   return user
end

function set_cookie()
   local expires_after = 3600
   local expiration = ngx.time() + expires_after
   local token = expiration .. ":" .. ngx.encode_base64(ngx.hmac_sha1(
       ngx.var.lua_auth_secret,
       tostring(expiration)))
   local cookie = "Auth=" .. token .. "; "
   -- @TODO: Don't include subdomains
   cookie = cookie .. "Path=/; Domain=" .. ngx.var.server_name .. "; "
   cookie = cookie .. "Expires=" .. ngx.cookie_time(expiration) .. "; "
   cookie = cookie .. "; Max-Age=" .. expires_after .. "; HttpOnly"
   ngx.header['Set-Cookie'] = cookie
end

local user = get_user()

if user then
   ngx.log(ngx.INFO, 'Authenticated user "' .. user .. '"')
   set_cookie()
   ngx.header.content_type = 'text/html'
   ngx.say("<html><head><script>location.reload()</script></head></html>")
else
   ngx.header.content_type = 'text/plain'
   ngx.header.www_authenticate = 'Basic realm=""'
   ngx.status = ngx.HTTP_UNAUTHORIZED
   ngx.say('401 Access Denied')
end
