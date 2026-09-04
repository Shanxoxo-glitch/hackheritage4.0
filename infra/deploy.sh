#!/bin/bash
echo 'Deploying stack...'
git pull origin main
docker compose up -d --build
