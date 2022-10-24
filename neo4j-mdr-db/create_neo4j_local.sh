#!/usr/bin/env bash

# Remove neo4j_local if it already exists
docker rm  neo4j_local

# Source env file
source .env

# Database directory
DATA=$(pwd)/data
# Plugins directory
PLUGINS=$(pwd)/plugins
# Import directory
IMPORT=$(pwd)/import_files
# Load scripts directory
SCRIPTS=$(pwd)/load_scripts
#

# User and Group
USER_AND_GROUP="$(id -u):$(id -g)"
#echo $USER_AND_GROUP

# Make sure direcories exist
if [ ! -d data ]; then
  mkdir -p data;
fi 

if [ ! -d plugins ]; then
  mkdir -p plugins;
fi 

if [ ! -d import_files ]; then
  mkdir -p import_files;
fi 

if [ ! -d load_scripts ]; then
  mkdir -p load_scripts;
fi 

#
# Run neo4j

docker run -d \
    --user=$USER_AND_GROUP \
    --name neo4j_local \
    -p$NEO4J_MDR_HTTP_PORT:7474 -p$NEO4J_MDR_HTTPS_PORT:7473 -p$NEO4J_MDR_BOLT_PORT:7687 \
    -v $DATA:/data \
    -v $PLUGINS:/plugins \
    -v $IMPORT:/var/lib/neo4j/import \
    -v $SCRIPTS:/var/lib/neo4j/load_scripts \
    -v /etc/ssl/certs:/etc/ssl/certs \
    -e NEO4J_AUTH=$NEO4J_MDR_AUTH_USER/$NEO4J_MDR_AUTH_PASSWORD \
    -e NEO4J_ACCEPT_LICENSE_AGREEMENT=yes \
    -e NEO4J_apoc_import_file_enabled=true \
    -e NEO4J_apoc_export_file_enabled=true \
    -e NEO4J_apoc_trigger_enabled=true \
    -e NEO4J_dbms_memory_heap_max__size=2g \
    -e NEO4J_dbms_memory_pagecache_size=4g \
    -e NEO4J_dbms_allow__upgrade=true\
    -e NEO4J_dbms_connector_bolt_advertised__address=$NEO4J_MDR_HOST:$NEO4J_MDR_BOLT_PORT \
    -e NEO4J_dbms_connector_http_advertised__address=$NEO4J_MDR_HOST:$NEO4J_MDR_HTTP_PORT \
    -e NEO4J_dbms_connector_https_advertised__address=$NEO4J_MDR_HOST:$NEO4J_MDR_HTTPS_PORT \
    -e NEO4J_metrics_prometheus_enabled=true \
    -e NEO4J_metrics_prometheus_endpoint=0.0.0.0:2004 \
    --env=NEO4JLABS_PLUGINS='["apoc"]' \
    neo4j:4.4.7-enterprise
