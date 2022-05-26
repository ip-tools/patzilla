# -*- coding: utf-8 -*-
# (c) 2015-2022 Andreas Motl <andreas.motl@ip-tools.org>
from patzilla.boot.cache import configure_cache_backend
from .client_api import espacenet_abstract
from .client_html import espacenet_description, espacenet_claims


if __name__ == '__main__':
    """
    python -m patzilla.access.epo.espacenet.api
    """
    configure_cache_backend()
    numbers = [
        "US5770123A",
        "US6269530B1",
        "DE19814298A1",
        "DE29624638U1",
        "EP0666666B1"
    ]
    for number in numbers:
        print("\n")
        print("## {}".format(number))
        print("")

        print("### Abstract")
        try:
            print(espacenet_abstract(number))
        except Exception as ex:
            print("ERROR: {}".format(ex))
        print("")

        print("### Claims")
        print(espacenet_claims(number))
        print("")

        print("### Description")
        print(espacenet_description(number))
        print("")
