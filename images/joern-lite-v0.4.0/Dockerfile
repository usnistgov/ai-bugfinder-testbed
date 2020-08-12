FROM alpine:3.12

# Build parameters
ARG JOERN_VERSION="fd9d01c"
ARG JOERN_TARBALL="${JOERN_VERSION}.tar.gz"
ARG JOERN_REPO="https://github.com/octopus-platform/joern"
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
    && git checkout ${JOERN_VERSION}

COPY build.gradle /tmp/${JOERN_DIR}

RUN cd /tmp/${JOERN_DIR} \
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