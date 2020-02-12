#!/bin/bash

set -e
set -u

readonly COMMENTS_URL="https://api.github.com/repos/hiranya911/firecloud/issues/${PR_NUMBER}/comments"
readonly STATUS=" github-actions\\[bot\\] Staging successful$"
readonly JQ_PATTERN=".[] | (.id|tostring) + \" \" + .user.login + \" \" + .body[0:50]"
readonly STATUS_UPDATED=`curl -s ${COMMENTS_URL} | jq -r "${JQ_PATTERN}" | grep "${STATUS}"` || true
if [[ -z "${STATUS_UPDATED}" ]]; then
    if [[ -n "${STAGING_SUCCESSFUL}" ]]; then
        echo "Adding comment"
        curl "${COMMENTS_URL}" \
            -s \
            -d '{"body": "Staging successful"}' \
            -o /dev/null \
            -H "Authorization: Bearer ${GITHUB_TOKEN}"
    fi
else
    if [[ -z "${STAGING_SUCCESSFUL}" ]]; then
        readonly COMMENT_ID=`echo ${STATUS_UPDATED} | awk '{print $1}'`
        echo "Deleting comment ${COMMENT_ID}"
        curl "https://api.github.com/repos/hiranya911/firecloud/issues/comments/${COMMENT_ID}" \
            -s \
            -X DELETE \
            -o /dev/null \
            -H "Authorization: Bearer ${GITHUB_TOKEN}"
    fi
fi