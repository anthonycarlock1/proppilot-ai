#!/bin/sh
set -eu
if [ "${1:-serve}" != serve ]; then
    echo 'Expected serve argument' >&2
    exit 1
fi
exec uvicorn "${HOSTING_APP:-ml.serving.app:app}" --host 0.0.0.0 --port 8080 --workers 1
