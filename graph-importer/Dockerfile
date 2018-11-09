FROM alpine:3.8

# Build parameters
ARG JOERN_VERSION="0.3.1"
ARG JOERN_TARBALL="${JOERN_VERSION}.tar.gz"
ARG JOERN_REPO="https://github.com/fabsx00/joern/archive/${JOERN_TARBALL}"
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
    && mv ./bin/joern.jar /usr/local/bin \
    && rm -rf /tmp/*

# Setup the workir and entrypoint
WORKDIR /code
ENTRYPOINT [ \
  "java", "-Xmx4G", "-jar", "/usr/local/bin/joern.jar", \
  "-outdir", "/code/joern.db", "/code" \
]
