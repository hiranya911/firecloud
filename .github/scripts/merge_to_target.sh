#!/bin/bash

set -e
set -u

git config user.name "${GITHUB_ACTOR}"
git config user.email "${GITHUB_ACTOR}@users.noreply.github.com"
git remote set-url origin https://x-access-token:${GITHUB_TOKEN}@github.com/${GITHUB_REPOSITORY}.git

echo "Fetching dev..."
git fetch origin dev --unshallow

echo "Fetching test-target..."
git fetch origin test-target

echo "Switching to master..."
git checkout test-target

echo "Merging dev to test-target..."
git merge dev

echo "Pushing test-target..."
git push origin test-target
