# -*- coding: utf-8 -*-
# (c) 2026 Andreas Motl <andreas.motl@ip-tools.org>
"""
HTTP ``Accept`` header negotiation, following RFC 7231, section 5.3.2.

Semantics are aligned with ``webob.acceptparse``, which has been used before:
A missing or invalid header accepts everything.
"""
import typing as t


def _parse_media_range(item: str) -> t.Optional[t.Tuple[str, str, t.Dict[str, str], float]]:
    parts = [part.strip() for part in item.split(";")]
    media_range = parts[0].lower()
    if "/" not in media_range:
        return None
    main_type, sub_type = media_range.split("/", 1)
    if not main_type or not sub_type or (main_type == "*" and sub_type != "*"):
        return None
    quality = 1.0
    params: t.Dict[str, str] = {}
    for param in parts[1:]:
        key, _, value = param.partition("=")
        key = key.strip().lower()
        value = value.strip().strip('"')
        if key == "q":
            try:
                quality = float(value)
            except ValueError:
                return None
            if not 0.0 <= quality <= 1.0:
                return None
            # Accept extensions after ``q`` are not relevant for matching.
            break
        if key:
            params[key] = value
    return main_type, sub_type, params, quality


class Accept:
    """
    Parsed representation of an ``Accept`` header.
    """

    def __init__(self, header_value: t.Optional[str]):
        self.header_value = header_value
        self.ranges: t.Optional[t.List[t.Tuple[str, str, t.Dict[str, str], float]]] = None
        if header_value is not None and header_value.strip():
            ranges = []
            for item in header_value.split(","):
                if not item.strip():
                    continue
                parsed = _parse_media_range(item)
                if parsed is None:
                    # Invalid header: Treat like a missing one, as WebOb does.
                    ranges = None
                    break
                ranges.append(parsed)
            self.ranges = ranges

    def __bool__(self) -> bool:
        return self.ranges is not None

    def _quality(self, offer: str) -> float:
        """
        Compute the quality factor the client assigns to the given offer,
        using the most specific matching media range.
        """
        if self.ranges is None:
            return 1.0
        offer_type, _, offer_params_raw = offer.partition(";")
        offer_main, _, offer_sub = offer_type.strip().lower().partition("/")
        best_specificity = -1
        best_quality = 0.0
        for main_type, sub_type, params, quality in self.ranges:
            if main_type == "*":
                specificity = 0
            elif main_type == offer_main and sub_type == "*":
                specificity = 1
            elif main_type == offer_main and sub_type == offer_sub:
                specificity = 2 + len(params)
            else:
                continue
            if specificity > best_specificity:
                best_specificity = specificity
                best_quality = quality
        return best_quality

    def acceptable_offers(self, offers: t.Iterable[str]) -> t.List[t.Tuple[str, float]]:
        """
        Return the acceptable offers as ``(offer, quality)`` tuples, sorted by
        descending quality. Ties retain the order of the given offers.
        """
        results = []
        for index, offer in enumerate(offers):
            quality = self._quality(offer)
            if quality > 0:
                results.append((quality, index, offer))
        results.sort(key=lambda item: (-item[0], item[1]))
        return [(offer, quality) for quality, _, offer in results]

    def best_match(self, offers: t.Iterable[str], default_match: t.Optional[str] = None) -> t.Optional[str]:
        acceptable = self.acceptable_offers(offers)
        if acceptable:
            return acceptable[0][0]
        return default_match

    def __contains__(self, offer: str) -> bool:
        return self._quality(offer) > 0

    def __str__(self) -> str:
        return self.header_value or ""
