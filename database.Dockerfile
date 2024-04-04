ARG NEO4J_IMAGE=neo4j:5.10.0-enterprise
ARG PYTHON_IMAGE=python:3.11.3-slim

# --- Build stage ----
FROM $PYTHON_IMAGE as build-stage

ARG NEO4J_DOWNLOAD_URL=https://dist.neo4j.org/neo4j-enterprise-5.10.0-unix.tar.gz
ARG NEO4J_CHECKSUM=3d387334532ff35c6114343fadea68657f0c600665daa5af75fce96c087c6ddc

## Install required system packages, for clinical-mdr-api as well
RUN apt-get update \
    && apt-get -y install \
        ca-certificates-java \
        openjdk-17-jre-headless \
        git \
        curl \
        python3-cffi \
        python3-brotli \
        libpango-1.0-0 \
        libharfbuzz0b \
        libpangoft2-1.0-0 \
        jq \
    && pip install --upgrade pip pipenv wheel \
    && apt-get clean && rm -rf /var/lib/apt/lists && rm -rf ~/.cache

WORKDIR /neo4j

ARG NEO4J_server_memory_heap_initial__size="2G"
ARG NEO4J_server_memory_heap_max__size="2G"
ARG NEO4J_server_memory_pagecache_size="1G"

# Install Neo4j from tarball
RUN curl --fail --location --output neo4j.tar.gz --silent --show-error "$NEO4J_DOWNLOAD_URL" \
    && echo "$NEO4J_CHECKSUM  neo4j.tar.gz" | sha256sum --check - \
    && tar --extract --gzip --file neo4j.tar.gz --strip-components=1 \
    && rm neo4j.tar.gz \
    && mv labs/apoc*core.jar plugins/ \
    && neo4j_conf=/neo4j/conf/neo4j.conf \
    && echo "server.memory.heap.initial_size=$NEO4J_server_memory_heap_initial__size" >> $neo4j_conf \
    && echo "server.memory.heap.max_size=$NEO4J_server_memory_heap_max__size" >> $neo4j_conf \
    && echo "server.memory.pagecache.size=$NEO4J_server_memory_pagecache_size" >> $neo4j_conf \
    && echo 'dbms.security.procedures.unrestricted=algo.*,apoc.*' >> $neo4j_conf

WORKDIR /build

# Copy Pipfiles
COPY ./neo4j-mdr-db/Pipfile* neo4j-mdr-db/
COPY ./mdr-standards-import/Pipfile* mdr-standards-import/

# Install dependencies
RUN cd neo4j-mdr-db && pipenv sync \
    && cd ../mdr-standards-import && pipenv sync \
    && rm -rf ~/.cache

# Copy program files
COPY ./neo4j-mdr-db neo4j-mdr-db
COPY ./mdr-standards-import mdr-standards-import

# Copy environment file
COPY ./studybuilder-import/.env.import mdr-standards-import/.env

ARG CDISC_DATA_DIR="mdr_standards_import/container_booting/"
ARG NEO4J_MDR_AUTH_PASSWORD="changeme1234"

ENV NEO4J_MDR_BOLT_PORT=7687 \
    NEO4J_MDR_HTTP_PORT=7674 \
    NEO4J_MDR_HTTPS_PORT=7673 \
    NEO4J_MDR_HOST=localhost \
    NEO4J_MDR_AUTH_USER=neo4j \
    NEO4J_MDR_DATABASE=mdrdb \
    NEO4J_CDISC_IMPORT_BOLT_PORT=7687 \
    NEO4J_CDISC_IMPORT_HOST=localhost \
    NEO4J_CDISC_IMPORT_AUTH_USER=neo4j \
    NEO4J_CDISC_IMPORT_AUTH_PASSWORD=$NEO4J_MDR_AUTH_PASSWORD \
    NEO4J_CDISC_IMPORT_DATABASE=cdisc-import \
    NEO4J_ACCEPT_LICENSE_AGREEMENT=yes

ARG reportDate="2024-01-05 14:54:32 +0100"

# Start Neo4j then run init and import
RUN /neo4j/bin/neo4j-admin dbms set-initial-password "$NEO4J_MDR_AUTH_PASSWORD" \
    # start neo4j server
    && /neo4j/bin/neo4j console & neo4j_pid=$! \
    && trap "kill -TERM $neo4j_pid" EXIT \
    # wait until $NEO4J_MDR_BOLT_PORT 7687/tcp is open
    && while ! grep -qF "$(printf ':%04X' "$NEO4J_MDR_BOLT_PORT")" /proc/net/tcp; do sleep 2; done \
    && set -x \
    # init database
    && cd neo4j-mdr-db && pipenv run init_neo4j \
    # import neodash reports
    && mkdir -p neodash_reports/import && FILES="neodash_reports/*LATEST.json" \
    && for f in $FILES; do echo "Processing $f file..."; filename=`basename $f` content=`cat $f` ; \
    title=`jq -r .title $f`; uuid=`jq -r .uuid $f`; version=`jq -r .version $f`; echo "$title" "$uuid" "$version"; \
    jq -n --slurpfile content $f --arg title "$title" --arg uuid "$uuid" --arg version "$version" --arg date "$reportDate" '. += {"content": $content, "title": $title, "uuid": $uuid, "version": $version, "date": $date, "user": "kwl@novonordisk.com"}' > neodash_reports/import/$filename; \
    done \
    && python -m pipenv run import_reports neodash_reports/import \
    # imports
    && cd ../mdr-standards-import && pipenv run pipeline_bulk_import "IMPORT" "packages" true \
    # stop neo4j server gently, but first wait a little for recent transactions to finish
    && sleep 60 && kill -TERM $neo4j_pid && wait $neo4j_pid \
    && trap EXIT

# Install dependencies
COPY ./studybuilder-import/Pipfile* studybuilder-import/
COPY ./clinical-mdr-api/Pipfile* clinical-mdr-api/
RUN cd studybuilder-import && pipenv sync \
    && cd ../clinical-mdr-api && pipenv sync \
    && rm -rf ~/.cache

# Copy program files
COPY ./studybuilder-import studybuilder-import
COPY ./clinical-mdr-api clinical-mdr-api

# Set up environments
COPY ./studybuilder-import/.env.import studybuilder-import/.env

ENV NEO4J_DSN="bolt://${NEO4J_MDR_AUTH_USER}:${NEO4J_MDR_AUTH_PASSWORD}@localhost:7687/" \
    NEO4J_DATABASE=mdrdb \
    OAUTH_ENABLED=false \
    ALLOW_ORIGIN_REGEX=".*"

# Start Neo4j and API and do the studybuilder-import
RUN /neo4j/bin/neo4j console & neo4j_pid=$! \
    && trap "kill -TERM $api_pid $neo4j_pid" EXIT \
    # wait until $NEO4J_MDR_BOLT_PORT 7687/tcp is open
    && while ! grep -qF "$(printf ':%04X' "$NEO4J_MDR_BOLT_PORT")" /proc/net/tcp; do sleep 2; done \
    # start API
    && sleep 60 && { cd clinical-mdr-api && pipenv run uvicorn --host 127.0.0.1 --port 8000 --log-level info clinical_mdr_api.main:app & api_pid=$! ;} \
    # wait until 8000/tcp is open (hex 1F40)
    && while ! grep -qF "$(printf ':%04X' 8000)" /proc/net/tcp; do sleep 2; done \
    && set -x \
    # imports
    && sleep 60 && cd studybuilder-import && pipenv run import_all \
    # stop the api
    && sleep 10 && kill -TERM $api_pid && wait $api_pid \
    # stop neo4j server gently, but first wait a little for recent transactions to finish
    && sleep 30 && kill -TERM $neo4j_pid && wait $neo4j_pid \
    && trap EXIT


# --- Prod stage ----
# Copy database directory from build-stage to the official neo4j docker image
FROM $NEO4J_IMAGE as production-stage

ARG UID=1000
ARG USER=neo4j
ARG GROUP=neo4j

# Match id of neo4j user with the current user on the host for correct premissions of db dumps mounted folder
ARG UID=1000
RUN [ "x$UID" = "x1000" ] || { \
        echo "Changing uid & gid of neo4j user to $UID" \
        && usermod --uid "$UID" "neo4j" \
        && groupmod --gid "$UID" "neo4j" \
    ;}

# Install APOC plugin
RUN wget --quiet --timeout 60 --tries 2 --output-document /var/lib/neo4j/plugins/apoc.jar \
    https://github.com/neo4j/apoc/releases/download/5.10.1/apoc-5.10.1-core.jar

# Copy database files from build stage
COPY --from=build-stage --chown=$USER:$GROUP /neo4j/data /data

# Set up default environment variables
ENV NEO4J_apoc_trigger_enabled="true" \
    NEO4J_apoc_import_file_enabled="true" \
    NEO4J_apoc_export_file_enabled="true"

# Volume attachment point: if an empty volume is mounted, it gets populated with the pre-built database from the image
VOLUME /data

# run as non root user
USER $USER

HEALTHCHECK --start-period=60s --timeout=3s --interval=10s --retries=3 \
    CMD wget --quiet --spider --timeout 2 --tries 1 "http://localhost:7474/" || exit 1
