-- -*- coding: utf-8 -*-
-- (c) 2014 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>

-- our static user database ;]
local users = { foo = "bar" };

config = {

    auth = {

        -- the secret used for signing cookies with hmac
        hmac_secret = 'franz jagt im komplett verwahrlosten taxi quer durch bayern.',

        -- http basic authentication
        --mode = 'basic-auth',

        -- login-form authentication
        mode = 'login-form',
    },

    users = users,
};

return config;
