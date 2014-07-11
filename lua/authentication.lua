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
   if ngx.var.users[user] ~= pass
      return
   end

   return user
end

function set_cookie()
   local expires_after = 3600
   local expiration = ngx.time() + expires_after
   local token = expiration .. ":" .. ngx.encode_base64(ngx.hmac_sha1(
       ngx.var.lua_auth_secret,
       expiration))
   local cookie = "Auth=" .. token .. "; "
   -- @TODO: Don't include subdomains
   cookie = cookie .. "Path=/; Domain=" .. ngx.var.server_name .. "; "
   cookie = cookie .. "Expires=" .. ngx.cookie_time(expiration) .. "; "
   cookie = cookie .. "; Max-Age=" .. expires_after .. "; HttpOnly"
   ngx.header['Set-Cookie'] = cookie
end

local user = get_user()

if user then
   ngx.log(ngx.INFO, 'Authenticated' .. user)
   set_cookie()
   ngx.header.content_type = 'text/html'
   ngx.say("<html><head><script>location.reload()</script></head></html>")
else
   ngx.header.content_type = 'text/plain'
   ngx.header.www_authenticate = 'Basic realm=""'
   ngx.status = ngx.HTTP_UNAUTHORIZED
   ngx.say('401 Access Denied')
end
