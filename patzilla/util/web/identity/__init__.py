# -*- coding: utf-8 -*-
# (c) 2014 Andreas Motl, Elmyra UG

# ------------------------------------------
#   bootstrapping
# ------------------------------------------
def setup(registry):
    registry.include("patzilla.util.web.identity.store")
    registry.include("patzilla.util.web.identity.service")
