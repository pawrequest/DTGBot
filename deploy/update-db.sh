SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

docker run --rm \
  -v "$SCRIPT_DIR/../reddit.env":/app/reddit.env \
  -v "$SCRIPT_DIR/../data":/app/guru_data \
  -e REDDIT_ENV=/app/reddit.env \
  -e GURU_DATA=/app/guru_data \
  dtgbot:latest update-db