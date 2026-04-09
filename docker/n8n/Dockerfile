ARG N8N_VERSION=2.2.6
FROM docker.n8n.io/n8nio/n8n:${N8N_VERSION} AS upstream

FROM alpine:3.22

COPY --from=upstream / /

ENV NPM_CONFIG_UPDATE_NOTIFIER=false \
    YARN_DISABLE_SELF_UPDATE_CHECK=true \
    NODE_ICU_DATA=/usr/local/lib/node_modules/full-icu \
    NODE_ENV=production \
    N8N_RELEASE_TYPE=stable \
    SHELL=/bin/sh

WORKDIR /home/node

USER root

RUN apk add --no-cache \
    bash \
    curl \
    jq \
    tzdata && \
    mkdir -p /files && \
    chown -R node:node /files

EXPOSE 5678

USER node

ENTRYPOINT ["tini", "--", "/docker-entrypoint.sh"]
