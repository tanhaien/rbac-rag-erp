#!/bin/bash

# This script is used to set up the development environment.

# Install backend dependencies
pip install -r backend/requirements.txt

# Install frontend dependencies
cd frontend && npm install && cd ..
