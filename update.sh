#!/bin/bash

git pull

docker-compose -f docker-compose_docker-servers.yml down &&
docker-compose -f docker-compose_docker-servers.yml up --build -d