#!/bin/bash

set -e
set -u

git config user.name "${GITHUB_ACTOR}"
git config user.email "${GITHUB_ACTOR}@users.noreply.github.com"
git remote set-url origin https://x-access-token:${GITHUB_TOKEN}@github.com/${GITHUB_REPOSITORY}.git

git fetch origin dev --unshallow
git fetch origin test-target --unshallow

git checkout master
git merge dev

git push origin test-target
