-- -*- coding: utf-8 -*-
-- (c) 2014 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>

-- our static user database ;]
local users = { foo = "bar" };

config = {

    auth = {

        -- http basic authentication
        --mode = 'basic-auth',

        -- login-form authentication
        mode = 'login-form',

        -- secret used for signing cookies with hmac
        hmac_secret = 'franz jagt im komplett verwahrlosten taxi quer durch bayern.',

        -- cookie expiration time
        --cookie_expiration = 60 * 60,    -- 1 hour
        cookie_expiration = 1 * 60,     -- 1 minute

        -- name of the cookie
        cookie_name = 'Auth',
    },

    users = users,
};

return config;
