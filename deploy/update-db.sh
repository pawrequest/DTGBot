#!/bin/sh
docker run --rm \
  -v "$(pwd)/../reddit.env":/app/reddit.env \
  -v "$(pwd)/../data":/app/guru_data \
  -e REDDIT_ENV=/app/reddit.env \
  -e GURU_DATA=/app/guru_data \
  dtgbot:latest update-db