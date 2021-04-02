FROM python:3.8-alpine as builder

RUN apk add --update --no-cache cmake make git openssh bash gcc g++ musl-dev linux-headers mariadb-dev libffi-dev rust cargo flex bison

ARG CI_REGISTRY_USER
ARG CI_JOB_TOKEN
ARG CI_PROJECT_ID
ARG CI_REPOSITORY_PYPI_URL


# force using bash shell
SHELL ["/bin/bash", "-c"]

# useful environment variables
ENV VENV=/wwpdb/onedep/venv
ENV PATH="$VENV/bin:$PATH"

RUN python -m venv $VENV

# setup pip
RUN pip config --site set global.extra-index-url https://${CI_REGISTRY_USER}:${CI_JOB_TOKEN}@${CI_REPOSITORY_PYPI_URL}/simple
RUN pip config --site set global.no-cache-dir false

# install the server
WORKDIR /checkouts
COPY . .
RUN pip --no-cache-dir install .

# install gunicorn for serving the wsgi scripts
RUN pip install gunicorn

FROM python:3.8-alpine

RUN apk add --update --no-cache bash mariadb-dev

# force using bash shell
SHELL ["/bin/bash", "-c"]

ENV ONEDEP_PATH=/wwpdb/onedep
ENV VENV=$ONEDEP_PATH/venv
ENV PATH="$VENV/bin:$PATH"

ENV SITE_CONFIG='. ${TOP_WWPDB_SITE_CONFIG_DIR}/init/env.sh --siteid ${WWPDB_SITE_ID} --location ${WWPDB_SITE_LOC}'
ENV WRITE_SITE_CONFIG_CACHE='ConfigInfoFileExec --siteid $WWPDB_SITE_ID --locid $WWPDB_SITE_LOC --writecache'

WORKDIR ${ONEDEP_PATH}
COPY --from=builder ${ONEDEP_PATH} .

ENV RUN_SCRIPT=${SITE_CONFIG_PATH}/run_server.sh
RUN echo "${SITE_CONFIG}" >> ${RUN_SCRIPT} \
    && echo "gunicorn wwpdb.apps.workmanager.webapp.wsgi --bind 0.0.0.0:8000 --timeout 0 --threads 4" >> ${RUN_SCRIPT} \
    && chmod a+x ${RUN_SCRIPT}

CMD ${RUN_SCRIPT}


