#!/bin/bash

RELEASE_VERSION=`python -c "execfile('release_demo/__about__.py'); print(__version__)"`
echo "Releasing version ${RELEASE_VERSION}"

RELEASE_TAG=`git describe --tags v${RELEASE_VERSION} 2> /dev/null`
if [[ $? -eq 0 ]];
then
    echo "Tag v${RELEASE_VERSION} already exists."
    if [[ -z "${RETRY_RELEASE}" ]];
    then
        echo "RETRY_RELEASE option is not set. Exiting."
        exit 1
    else
        echo "RETRY_RELEASE option is set. Releasing from the existing tag."
        REUSE_RELEASE_TAG=1
    fi
fi

if [[ -z "${REUSE_RELEASE_TAG}" ]];
then
    echo "Running unit tests..."
    echo "Running integration tests..."
    echo "Creating new tag v${RELEASE_VERSION}"
fi

git checkout v${RELEASE_VERSION}
echo "Creating release artifacts..."
echo "Uploading artifacts to Pypi..."
echo "Done."
