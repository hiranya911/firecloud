#!/bin/bash

echo "Release version is ${RELEASE_VERSION}"
echo "Retry release is set to ${RETRY_RELEASE}"

git fetch --depth=1 origin +refs/tags/*:refs/tags/*

RELEASE_TAG=`git describe --tags ${RELEASE_VERSION} 2> /dev/null`
if [[ $? -eq 0 ]];
then
    echo "Tag ${RELEASE_VERSION} already exists."
    if [[ "${RETRY_RELEASE}" != "true" ]];
    then
        echo "RETRY_RELEASE option is not set. Exiting."
        exit 1
    else
        echo "RETRY_RELEASE option is set. Releasing from the existing tag."
        echo "::set-output name=scratch::false"
    fi
else
    echo "Tag ${RELEASE_VERSION} does not exist. It will be created."
    echo "::set-output name=scratch::true"
fi