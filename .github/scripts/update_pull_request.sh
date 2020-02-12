#!/bin/bash

set -e
set -u

readonly STATUS_CODE=`curl "${COMMENTS_URL}" \
    -s \
    -d "{\"body\": \"${MESSAGE}\"}" \
    --write-out "%{http_code}" \
    -o /dev/null \
    -H "Authorization: Bearer ${GITHUB_TOKEN}" \
    -H "Content-type: application/json"`

if [[ "${STATUS_CODE}" -ne 201 ]]; then
    echo "Request failed with status: ${STATUS_CODE}"
    exit 1
fi
