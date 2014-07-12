-- -*- coding: utf-8 -*-
-- (c) 2014 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>

-- our static user database ;]
local users = { foo = "bar" };

config = {
    --authmode = 'basic-auth',
    authmode = 'login-form',
    users = users,
};

return config;
