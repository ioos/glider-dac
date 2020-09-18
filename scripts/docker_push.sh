#!/bin/bash

# Dockerhub login
if [[ ! -n "$DOCKER_PASSWORD" || ! -n "$DOCKER_USERNAME" ]]; then
  echo "DOCKER_USERNAME and DOCKER_PASSWORD must be set as environment variables!" >&2
  exit 1
else
  docker login -u "$DOCKER_USERNAME" --password-stdin <<< "$DOCKER_PASSWORD"

  if [[ $? -ne 0 ]]; then
    exit 1
  fi

  # if the build is for a pushed tag, use that tag for the Docker image;
  # otherwise, use "latest (via BASH substitution)"
  image_release_tag="${TRAVIS_TAG:-latest}"

  echo "Tagging image with: $image_release_tag"
  docker tag glider-dac:latest ioos/glider-dac:$image_release_tag
  docker push ioos/glider-dac
fi