FROM alpine:3.8

# Build parameters
#ARG JOERN_VERSION="0.3.1"
ARG JOERN_VERSION="0bcf0c4"
ARG JOERN_TARBALL="${JOERN_VERSION}.tar.gz"
#ARG JOERN_REPO="https://github.com/fabsx00/joern/archive/${JOERN_TARBALL}"
ARG JOERN_REPO="https://github.com/octopus-platform/joern"
#ARG JOERN_DIR="joern-${JOERN_VERSION}"
ARG JOERN_DIR="joern"
ARG JOERN_LIB_TARBALL="lib.tar.gz"
ARG JOERN_LIB_REPO="http://mlsec.org/joern/lib/${JOERN_LIB_TARBALL}"

# Install pre-requisites
RUN apk update \
    && apk add --no-cache \
        git \
        gradle \
        openjdk8 \
    && rm -rf /var/cache/apk/*

# Install Joern and cleanup
RUN cd /tmp \
    && git clone ${JOERN_REPO} \
    && cd ${JOERN_DIR} \
    && git checkout ${JOERN_VERSION} \
    && gradle build -p ./projects/extensions/joern-fuzzyc -x test \
    && gradle build -p ./projects/extensions/jpanlib -x test \
    && mv ./projects/extensions/joern-fuzzyc/build/libs/joern-fuzzyc.jar /usr/local/lib \
    && mv ./projects/extensions/joern-fuzzyc/lib/* /usr/local/lib \
    && mv ./projects/extensions/jpanlib/build/libs/jpanlib.jar /usr/local/lib \
    && rm -rf \
        /tmp/* \
        /root/.gradle \
    && apk del --no-cache \
        git \
        gradle

COPY convert.sh /usr/local/bin/

# Setup the workir and entrypoint
WORKDIR /code
ENTRYPOINT [ "/usr/local/bin/convert.sh" ]