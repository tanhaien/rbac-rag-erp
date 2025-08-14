#!/bin/bash

# This script is used to run database migrations.

docker-compose run backend alembic upgrade head
