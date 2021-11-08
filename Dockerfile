FROM alpine:3.14
# android-tools includes simg2img and img2simg
RUN apk update
RUN apk add zip android-tools brotli python3 py3-aiohttp file

RUN adduser -D -H gsitozip gsitozip

WORKDIR /usr/src/gsi2zip
COPY --chown=gsitozip:gsitozip . .

USER gsitozip

CMD [ "/usr/src/gsi2zip/web.py" ]