#!/bin/bash

###################################### Outputs #####################################

# 1. version: The version of this release including the 'v' prefix (e.g. v1.2.3).
# 2. publish: Set when not executing in the dryrun mode.
# 3. tweet: Set when the release should be posted to Twitter. Also implies
#    publish=true.
# 4. create_tag: Set when the release is not already tagged.
# 5. reuse_tag: Set when the release is already tagged.
# 6. directory: Directory where the release artifacts will be built. Either
#    'staging' or 'deploy'.

####################################################################################

echo "[release: dryrun]: ${DRYRUN_RELEASE}"
echo "[release: skip-tweet]: ${SKIP_TWEET}"
echo

# Find current version.
RELEASE_VERSION=`python -c "exec(open('release_demo/__about__.py').read()); print(__version__)"`
echo "Releasing version ${RELEASE_VERSION}"
echo "::set-output name=version::v${RELEASE_VERSION}"

# Fetch all tags.
git fetch --depth=1 origin +refs/tags/*:refs/tags/*

# Check if this release is already tagged.
git describe --tags v${RELEASE_VERSION} 2> /dev/null
if [[ $? -eq 0 ]]; then
  echo "Tag v${RELEASE_VERSION} already exists. Halting release process."
  echo "If the tag was created in a previous unsuccessful attempt, delete it and try again."
  echo "  $ git tag -d v${RELEASE_VERSION}"
  echo "  $ git push --delete origin v${RELEASE_VERSION}"
  exit 1
fi

echo "Tag v${RELEASE_VERSION} does not exist."

# Handle dryrun mode.
if [[ "$DRYRUN_RELEASE" == "true" ]]; then
  echo "Dryrun mode has been requested. No new tags or artifacts will be published."
  echo "::set-output name=directory::staging"
else
  echo "Dryrun mode has not been requested."
  echo "A new tag will be created, and release artifacts posted to Pypi."
  echo "::set-output name=publish::true"
  echo "::set-output name=directory::deploy"

  if [[ "${SKIP_TWEET}" != "true" ]]; then
    echo "Release will be posted to Twitter."
    echo "::set-output name=tweet::true"
  else
    echo "Skip Tweet mode has been requested. Release will not be posted to Twitter."
  fi
fi

git fetch origin master --prune --unshallow
CURRENT_DIR=$(dirname "$0")
CHANGELOG=`${CURRENT_DIR}/generate_changelog.sh`
echo "$CHANGELOG"
FILTERED_CHANGELOG=`echo "$CHANGELOG" | grep -v "\\[info\\]"`
FILTERED_CHANGELOG="${FILTERED_CHANGELOG//'%'/'%25'}"
FILTERED_CHANGELOG="${FILTERED_CHANGELOG//$'\n'/'%0A'}"
FILTERED_CHANGELOG="${FILTERED_CHANGELOG//$'\r'/'%0D'}"
echo "::set-output name=changelog::${FILTERED_CHANGELOG}"
