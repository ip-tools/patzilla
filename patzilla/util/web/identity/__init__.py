# -*- coding: utf-8 -*-
# (c) 2014 Andreas Motl, Elmyra UG

# ------------------------------------------
#   bootstrapping
# ------------------------------------------
def includeme(config):
    config.include(".store")
    config.include(".service")
    config.scan(".service")
