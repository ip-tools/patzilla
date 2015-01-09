#!/usr/bin/env python
# -*- coding: utf-8 -*-
# https://github.com/nltk/nltk/blob/develop/nltk/test/runtests.py
import sys
import logging
import nose
from nose.plugins.manager import PluginManager
from nose.plugins.doctests import Doctest
from nose.plugins import builtin
from nose_exclude import NoseExclude
from elmyra.ip.util.test.doctest_nose_plugin import DoctestFix

if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG)

    class CustomPluginManager(PluginManager):
        """
        Nose plugin manager that replaces standard doctest plugin with a patched version.
        """
        def loadPlugins(self):
            for plug in builtin.plugins:
                if plug != Doctest:
                    self.addPlugin(plug())
            self.addPlugin(DoctestFix())
            self.addPlugin(NoseExclude())
            super(CustomPluginManager, self).loadPlugins()

    manager = CustomPluginManager()
    manager.loadPlugins()

    args = sys.argv[1:]
    nose.main(argv=args, plugins=manager.plugins)
