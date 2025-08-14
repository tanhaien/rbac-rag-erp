#!/bin/bash

# This script is used to deploy the application.

docker-compose -f docker/docker-compose.prod.yml up -d --build
