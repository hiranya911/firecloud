#!/bin/bash

############################# Input environment variables ##########################

# 1. GITHUB_SHA: Git revision to release from (set by GitHub Actions).
# 2. GITHUB_ACTOR: User that triggered the release (set by GitHub Actions).
# 3. DRYRUN_RELEASE: "true" to run the workflow in the dryrun mode.
# 4. SKIP_TWEET: "true" to suppress the Tweet at the end of workflow.

###################################### Outputs #####################################

# 1. version: The version of this release including the 'v' prefix (e.g. v1.2.3).
# 2. publish: Set when not executing in the dryrun mode.
# 3. tweet: Set when the release should be posted to Twitter. Only set if
#    publish is also set.
# 4. changelog: Formatted changelog text for this release.

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


if [[ -z "${FIREBASE_GIT_REF:-}" ]]; then
    FIREBASE_GIT_REF="${GITHUB_REF}"
fi

if [[ -z "${FIREBASE_LABEL_TWEET:-}" ]]; then
    FIREBASE_LABEL_TWEET="false"
fi

if [[ -z "${FIREBASE_PR_TITLE:-}"  ]]; then
    FIREBASE_PR_TITLE=""
fi


echo_info "Starting release preflight..."
echo_info "Git revision          : ${GITHUB_SHA}"
echo_info "Git ref               : ${FIREBASE_GIT_REF}"
echo_info "Workflow triggered by : ${GITHUB_ACTOR}"
echo_info "GitHub event          : ${GITHUB_EVENT_NAME}"
if [[ "${GITHUB_EVENT_NAME}" == "pull_request" ]]; then
    echo_info "Pull request title    : ${FIREBASE_PR_TITLE}"
    echo_info "Label Tweet           : ${FIREBASE_LABEL_TWEET}"
fi


echo_info ""
echo_info "--------------------------------------------"
echo_info "Extracting release version"
echo_info "--------------------------------------------"
echo_info ""

readonly ABOUT_FILE="release_demo/__about__.py"
echo_info "Loading version from: ${ABOUT_FILE}"

readonly VERSION_SCRIPT="exec(open('${ABOUT_FILE}').read()); print(__version__)"
readonly RELEASE_VERSION=`python -c "${VERSION_SCRIPT}"` || true
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
echo_info "Processing workflow options"
echo_info "--------------------------------------------"
echo_info ""

PUBLISH_MODE=0

if [[ "${GITHUB_EVENT_NAME}" == "repository_dispatch" ]]; then
    echo_info "Workflow manually triggered via repository dispatch."
elif [[ "${GITHUB_EVENT_NAME}" == "pull_request" ]]; then
    if [[ "$GITHUB_REF" == "master" ]]; then
        readonly CHORE=`echo "${FIREBASE_PR_TITLE}" | grep "^\\[chore\\] Release .*"` || true
        if [[ -n "${CHORE}" ]]; then
            echo_info "Pull request title (${CHORE}) indicates intention to publish."
            PUBLISH_MODE=1
        else
            echo_info "Pull request title does not indicate intention to publish."
        fi
    else
        echo_info "Git ref (${GITHUB_REF}) is not eligible for publishing."
    fi
else
    echo_warn "Unsupported GitHub event: ${GITHUB_EVENT_NAME}"
    terminate
fi

if [[ $PUBLISH_MODE -eq 1 ]]; then
    echo_info "This is NOT a drill."
    echo_info "A new tag will be created, and release artifacts posted to Pypi."
    echo "::set-output name=publish::true"

    if [[ "${FIREBASE_LABEL_TWEET}" == "true" ]]; then
        echo_info "Release will be posted to Twitter upon successful completion."
        echo "::set-output name=tweet::true"
    else
        echo_info "Release will not be posted to Twitter."
    fi
else
    echo_info "Executing a dry run. No new tags or artifacts will be published."
fi


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
  if [[ ${PUBLISH_MODE} -eq 1 ]]; then
    echo_warn "Tag v${RELEASE_VERSION} already exists."
    echo_warn "If the tag was created in a previous failed attempt, delete it and try again."
    echo_warn "   $ git tag -d v${RELEASE_VERSION}"
    echo_warn "   $ git push --delete origin v${RELEASE_VERSION}"

    readonly RELEASE_URL="https://github.com/hiranya911/firecloud/releases/tag/v${RELEASE_VERSION}"
    echo_warn "Delete any corresponding releases at ${RELEASE_URL}"
    terminate
  fi

  echo_info "Tag v${RELEASE_VERSION} already exists. Ignoring in the dry run mode."
else
  echo_info "Tag v${RELEASE_VERSION} does not exist."
fi


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
