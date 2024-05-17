#!/bin/sh
docker run --rm \
  -v "$(pwd)/../reddit.env":/app/reddit.env \
  -v "$(pwd)/../data":/app/guru_data \
  dtgbot:latest update-db
