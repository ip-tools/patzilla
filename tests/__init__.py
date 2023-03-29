# -*- coding: utf-8 -*-
# (c) 2022 Andreas Motl <andreas.motl@ip-tools.org>
import warnings


def suppress_warnings():
    """
    Silence specific warnings.

    - DeprecationWarning: Importing from numpy.testing.nosetester is deprecated since 1.15.0, import from numpy.testing instead.
    """
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        import numpy.testing


suppress_warnings()
