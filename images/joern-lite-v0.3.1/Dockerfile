FROM alpine:3.12

# Build parameters
ARG JOERN_VERSION="0.3.1"
ARG JOERN_TARBALL="${JOERN_VERSION}.tar.gz"
ARG JOERN_REPO="https://github.com/octopus-platform/joern/archive/${JOERN_TARBALL}"
ARG JOERN_DIR="joern-${JOERN_VERSION}"
ARG JOERN_LIB_TARBALL="lib.tar.gz"
ARG JOERN_LIB_REPO="http://mlsec.org/joern/lib/${JOERN_LIB_TARBALL}"

# Install pre-requisites
RUN apk update \
    && apk add --no-cache \
        apache-ant \
        openjdk8 \
        wget \
    && rm -rf /var/cache/apk/*

# Install Joern
RUN cd /tmp \
    && wget ${JOERN_REPO} \
    && tar xfzv ${JOERN_TARBALL} \
    && cd ${JOERN_DIR} \
    && wget ${JOERN_LIB_REPO} \
    && tar xfzv ${JOERN_LIB_TARBALL} \
    && ant \
    && mv ./bin/joern.jar /usr/local/bin/ \
    && rm -rf /tmp/*

COPY convert.sh /usr/local/bin/

# Setup the workir and entrypoint
WORKDIR /code
ENTRYPOINT [ "/usr/local/bin/convert.sh" ]
