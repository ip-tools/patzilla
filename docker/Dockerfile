# Dockerfile for building Docker images for official releases of PatZilla.
#
# The `patzilla` package will be installed from PyPI,
# so this is not meant for develoment purposes.

FROM debian:bullseye-slim AS patzilla-baseline

RUN \
    apt-get update && \
    apt-get install --yes \
    wget \
    build-essential \
    python2 \
    python2-dev \
    libjpeg-dev \
    libfreetype-dev \
    liblcms2-dev \
    libtiff-dev \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    pdftk \
    poppler-utils \
    imagemagick \
    libreoffice \
    unoconv \
    && \
    wget https://bootstrap.pypa.io/pip/2.7/get-pip.py && \
    python2 get-pip.py && \
    rm -rf /var/cache/apt


FROM patzilla-baseline

RUN \
    pip install patzilla && \
    rm -r /root/.cache
