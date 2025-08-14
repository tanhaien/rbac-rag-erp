#!/bin/bash

# Backend linting and formatting script

echo "🔍 Running Ruff linting..."
ruff check .

echo "🎨 Running Black formatting..."
black .

echo "✨ Code quality check completed!"

