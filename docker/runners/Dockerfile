ARG N8N_VERSION=2.2.6
FROM n8nio/runners:${N8N_VERSION}

USER root

ARG JS_EXTRA_PACKAGES

RUN cd /opt/runners/task-runner-javascript && \
    if [ -n "${JS_EXTRA_PACKAGES}" ]; then pnpm add ${JS_EXTRA_PACKAGES}; fi

COPY docker/runners/n8n-task-runners.json /etc/n8n-task-runners.json

USER runner