#!/bin/bash

set -e
set -u

if [[ -n "${STAGING_SUCCESSFUL}" ]]; then
    readonly MESSAGE="Staging successful at ${HEAD_COMMIT_SHA}"
else
    readonly MESSAGE="Staging failed at ${HEAD_COMMIT_SHA}"
fi

curl "${COMMENTS_URL}" \
    -s \
    -d "{\"body\": \"${MESSAGE}\"}" \
    -o /dev/null \
    -H "Authorization: Bearer ${GITHUB_TOKEN}"
