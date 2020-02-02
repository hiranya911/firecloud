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


if [[ -z "${LABEL_DRY_RUN:-}" ]]; then
    LABEL_DRY_RUN="false"
fi

if [[ -z "${LABEL_SKIP_TWEET:-}" ]]; then
    LABEL_SKIP_TWEET="false"
fi


env


echo_info "Starting release preflight..."
echo_info "Git revision          : ${GITHUB_SHA}"
echo_info "Workflow triggered by : ${GITHUB_ACTOR}"
echo_info "GitHub event          : ${GITHUB_EVENT_NAME}"
echo_info "Label dry run         : ${LABEL_DRY_RUN}"
echo_info "Label skip Tweet      : ${LABEL_SKIP_TWEET}"


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

DRY_RUN_RELEASE=0

if [[ "${LABEL_DRY_RUN}" == "true" ]]; then
  DRY_RUN_RELEASE=1
  echo_info "Dry run label is set."
elif [[ "${GITHUB_EVENT_NAME}" == "repository_dispatch" ]]; then
  DRY_RUN_RELEASE=1
  echo_info "Workflow manually triggered via repository dispatch."
fi

if [[ $DRY_RUN_RELEASE -eq 0 ]]; then
  echo_info "A new tag will be created, and release artifacts posted to Pypi."
  echo "::set-output name=publish::true"

  if [[ "${LABEL_SKIP_TWEET}" == "true" ]]; then
    echo_info "Skip Tweet level is set."
    echo_info "Release will not be posted to Twitter."
  else
    echo_info "Release will be posted to Twitter upon successful completion."
    echo "::set-output name=tweet::true"
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
  if [[ ${DRY_RUN_RELEASE} -eq 0 ]]; then
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
