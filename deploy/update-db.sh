#!/bin/sh
docker run --rm \
  -v "${REDDIT_ENV}":/app/reddit.env \
  -v "${GURU_DATA}":/app/guru_data/ \
  -v "${GURU_FRONTEND}":/app/guru_fontend/ \
  dtgbot:latest run-updater
