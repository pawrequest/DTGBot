#!/bin/sh
docker run --rm \
  -v "../reddit.env":/app/reddit.env \
  -v "../data/":/app/guru_data/ \
  dtgbot:latest run-updater
