-- Some variable declarations.
local cookie = ngx.var.cookie_Auth
local hmac = ""
local timestamp = ""

if ngx.var.uri == "/auth" then
    return
end

-- Check that the cookie exists.
if cookie ~= nil and cookie:find(":") ~= nil then
    -- If there's a cookie, split off the HMAC signature
    -- and timestamp.
    local divider = cookie:find(":")
    hmac = ngx.decode_base64(cookie:sub(divider+1))
    timestamp = cookie:sub(0, divider-1)
    -- Verify that the signature is valid.
    if ngx.hmac_sha1(ngx.var.lua_auth_secret, timestamp) == hmac and tonumber(timestamp) >= ngx.time() then
       return
    end
end

-- Internally rewrite the URL so that we serve
-- /auth/ if there's no valid token.
ngx.exec("/auth")
