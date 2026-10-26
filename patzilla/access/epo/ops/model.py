# -*- coding: utf-8 -*-
# (c) 2022 Andreas Motl <andreas.motl@ip-tools.org>
from typing import List

import attr


@attr.define
class OpsFamilyAwareSearchResult:
    """
    Result model for function `patzilla.access.epo.ops.api:results_swap_family_members`.
    """
    data: List
    selected_numbers: List
    original_numbers: List
