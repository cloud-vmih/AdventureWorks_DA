#!/bin/bash

set -e

export PGUSER=postgres
psql -v ON_ERROR_STOP=1 <<- SHELL
  CREATE USER docker;
  CREATE DATABASE "Adventureworks";
  GRANT ALL PRIVILEGES ON DATABASE "Adventureworks" TO docker;
SHELL
cd /data
psql -v ON_ERROR_STOP=1 -d Adventureworks -f /data/install.sql
