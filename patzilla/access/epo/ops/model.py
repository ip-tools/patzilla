# -*- coding: utf-8 -*-
# (c) 2022 Andreas Motl <andreas.motl@ip-tools.org>
import attr


@attr.s
class OpsFamilyAwareSearchResult(object):
    """
    Result model for function `patzilla.access.epo.ops.api:results_swap_family_members`.
    """
    data = attr.ib(type=list)
    selected_numbers = attr.ib(type=list)
    original_numbers = attr.ib(type=list)
