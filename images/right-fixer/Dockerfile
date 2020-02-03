FROM alpine:3.11

RUN apk add --no-cache bash

COPY convert.sh /usr/bin/convert.sh

ENTRYPOINT ["/usr/bin/convert.sh"]