FROM alpine:3.7
RUN apk add --no-cache --update \
  bash \
  python2 \
  python2-dev \
  build-base \
  libffi-dev \
  openssl-dev \
  libxml2-dev \
  libxslt-dev \
  zlib-dev \
  pdftk \
  imagemagick && \
  python -m ensurepip && \
  rm -r /usr/lib/python*/ensurepip && \
  pip install --upgrade pip setuptools && \
  rm -r /root/.cache && \
  pip install patzilla
COPY patzilla.ini /patzilla.ini
CMD ["/usr/bin/pserve", "/patzilla.ini"]
EXPOSE 9999 6543