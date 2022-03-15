FROM debian:bullseye-slim

RUN apt update && \
    apt install zip brotli python3 python3-aiohttp file xz-utils -y

RUN useradd -m -s /bin/sh gsitozip

WORKDIR /usr/src/gsi2zip
COPY --chown=gsitozip:gsitozip . .

USER gsitozip

CMD [ "/usr/src/gsi2zip/web.py" ]
