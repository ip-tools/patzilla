-- -*- coding: utf-8 -*-
-- (c) 2014 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>

config = {

    auth = {

        -- http basic authentication
        --mode = 'basic-auth',

        -- login-form authentication
        mode = 'login-form',

        -- secret used for signing cookies with hmac
        hmac_secret = 'franz jagt im komplett verwahrlosten taxi quer durch bayern',

        -- cookie expiration time
        cookie_expiration   = 60 * 60 * 3,  -- 3 hours
        --cookie_expiration = 60 * 60,      -- 1 hour
        --cookie_expiration = 1 * 60,       -- 1 minute
        --cookie_expiration = 10,           -- 10 seconds

        -- cookie renewal threshold
        -- if expiration time delta is below this threshold, automatically issue a new cookie
        cookie_renewal      = 60 * 60,      -- 1 hour

        -- name of the cookie
        cookie_name = 'Auth',
    },

};

return config;
