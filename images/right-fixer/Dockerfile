FROM alpine:3.10

RUN apk add --no-cache bash

COPY convert.sh /usr/bin/convert.sh

ENTRYPOINT ["/usr/bin/convert.sh"]