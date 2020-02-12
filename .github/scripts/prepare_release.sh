#!/bin/bash

###################################### Outputs #####################################

# 1. version: The version of this release including the 'v' prefix (e.g. v1.2.3).
# 2. changelog: Formatted changelog text for this release.

####################################################################################

set -e
set -u

function echo_info() {
    local MESSAGE=$1
    echo "[INFO] ${MESSAGE}"
}

function echo_warn() {
    local MESSAGE=$1
    echo "[WARN] ${MESSAGE}"
}

function terminate() {
    echo ""
    echo_warn "--------------------------------------------"
    echo_warn "PREFLIGHT FAILED"
    echo_warn "--------------------------------------------"
    exit 1
}


echo_info "Starting release preflight..."
echo_info "Git revision          : ${GITHUB_SHA}"
echo_info "Workflow triggered by : ${GITHUB_ACTOR}"
echo_info "GitHub event          : ${GITHUB_EVENT_NAME}"
echo_info "GitHub ref            : ${GITHUB_REF}"


echo_info ""
echo_info "--------------------------------------------"
echo_info "Checking staging status"
echo_info "--------------------------------------------"
echo_info ""

curl ${COMMENTS_URL} -s -H "Authorization: Bearer ${GITHUB_TOKEN}" > comments.out

# Find the last comment made by the github-actions[bot]
readonly JQ_PATTERN="[.[] | select(.user.login==\"github-actions[bot]\").body] | last"
readonly LAST_COMMENT=`jq -r "${JQ_PATTERN}" comments.out` || true
readonly SUCCESS_PATTERN="^Staging successful at .*$"
if [[ "${LAST_COMMENT}" == "null" ]]; then
  echo_warn "Staging process clearance not found."
  terminate
elif ! [[ "${LAST_COMMENT}" =~ ${SUCCESS_PATTERN} ]]; then
  echo_warn "Staging process failed: ${LAST_COMMENT}"
  terminate
fi

readonly LAST_STAGED_COMMIT=`echo ${LAST_COMMENT} | awk '{print $NF}'`
echo_info "Release last staged at: ${LAST_STAGED_COMMIT}"

curl ${COMMITS_URL} -s -H "Authorization: Bearer ${GITHUB_TOKEN}" > commits.out

# Find the last commit made on the PR.
readonly LAST_COMMIT=`jq -r ".[-1].sha" commits.out` || true
echo_info "Last commit in the release PR: ${LAST_COMMIT}"

if [[ "${LAST_STAGED_COMMIT}" != "${LAST_COMMIT}" ]]; then
  echo_warn "Last commit on the PR does not match the last staged."
  terminate
fi


echo_info ""
echo_info "--------------------------------------------"
echo_info "Extracting release version"
echo_info "--------------------------------------------"
echo_info ""

readonly ABOUT_FILE="release_demo/__about__.py"
echo_info "Loading version from: ${ABOUT_FILE}"

readonly RELEASE_VERSION=`grep "__version__" ${ABOUT_FILE} | awk '{print $3}' | tr -d \'` || true
if [[ -z "${RELEASE_VERSION}" ]]; then
  echo_warn "Failed to extract release version from: ${ABOUT_FILE}"
  terminate
fi

if [[ ! "${RELEASE_VERSION}" =~ ^([0-9]*)\.([0-9]*)\.([0-9]*)$ ]]; then
  echo_warn "Malformed release version string: ${RELEASE_VERSION}"
  terminate
fi

echo_info "Extracted release version: ${RELEASE_VERSION}"
echo "::set-output name=version::v${RELEASE_VERSION}"


echo_info ""
echo_info "--------------------------------------------"
echo_info "Checking release tag"
echo_info "--------------------------------------------"
echo_info ""

echo_info "---< git fetch --depth=1 origin +refs/tags/*:refs/tags/* >---"
git fetch --depth=1 origin +refs/tags/*:refs/tags/*
echo ""

readonly EXISTING_TAG=`git rev-parse -q --verify "refs/tags/v${RELEASE_VERSION}"` || true
if [[ -n "${EXISTING_TAG}" ]]; then
  echo_warn "Tag v${RELEASE_VERSION} already exists."
  echo_warn "If the tag was created in a previous failed attempt, delete it and try again."
  echo_warn "   $ git tag -d v${RELEASE_VERSION}"
  echo_warn "   $ git push --delete origin v${RELEASE_VERSION}"

  readonly RELEASE_URL="https://github.com/hiranya911/firecloud/releases/tag/v${RELEASE_VERSION}"
  echo_warn "Delete any corresponding releases at ${RELEASE_URL}"
  terminate
fi

echo_info "Tag v${RELEASE_VERSION} does not exist."


echo_info ""
echo_info "--------------------------------------------"
echo_info "Generating changelog"
echo_info "--------------------------------------------"
echo_info ""

echo_info "---< git fetch origin master --prune --unshallow >---"
git fetch origin master --prune --unshallow
echo ""
echo_info "Generating changelog from history..."
readonly CURRENT_DIR=$(dirname "$0")
readonly CHANGELOG=`${CURRENT_DIR}/generate_changelog.sh`
echo "$CHANGELOG"

# Parse and preformat the text to handle multi-line output.
# See https://github.community/t5/GitHub-Actions/set-output-Truncates-Multiline-Strings/td-p/37870
FILTERED_CHANGELOG=`echo "$CHANGELOG" | grep -v "\\[INFO\\]"`
FILTERED_CHANGELOG="${FILTERED_CHANGELOG//'%'/'%25'}"
FILTERED_CHANGELOG="${FILTERED_CHANGELOG//$'\n'/'%0A'}"
FILTERED_CHANGELOG="${FILTERED_CHANGELOG//$'\r'/'%0D'}"
echo "::set-output name=changelog::${FILTERED_CHANGELOG}"


echo ""
echo_info "--------------------------------------------"
echo_info "PREFLIGHT SUCCESSFUL"
echo_info "--------------------------------------------"
