#!/bin/bash

set -e
set -u

readonly PR_NUMBER=`echo ${GITHUB_REF} | awk -F/ '{print $3}'`
readonly COMMENTS_URL="https://api.github.com/repos/hiranya911/firecloud/issues/${PR_NUMBER}/comments"

if [[ -n "${STAGING_SUCCESSFUL}" ]]; then
    readonly MESSAGE="Staging successful at ${GITHUB_SHA}"
else
    readonly MESSAGE="Staging failed at ${GITHUB_SHA}"
fi

curl "${COMMENTS_URL}" \
    -s \
    -d "{\"body\": \"${MESSAGE}\"}" \
    -o /dev/null \
    -H "Authorization: Bearer ${GITHUB_TOKEN}"
